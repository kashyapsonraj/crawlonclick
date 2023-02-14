import os
import json
import time

import requests

from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse, Http404
from django.core.mail import send_mail, EmailMessage
from core.db_util import MongoDBUtil
from core import config, logger, constant

from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

# stripe code
from django.conf import settings
import stripe
from django.urls import reverse


# Create your views here.
def index(request):
    template = 'index.html'
    return render(request, template)


def signup(request):
    signup_template = 'signup.html'
    signin_template = 'signin.html'
    if request.POST:
        data = request.POST
        user = User.objects.filter(email=data.get("email"))
        if user:
            return render(request, signin_template)
        else:
            user = User.objects.create_user(
                first_name=data.get("firstname"),
                last_name=data.get("lastname"),
                username=data.get("email"),
                email=data.get("email"),
                password=data.get("password")
            )
            user.save()
            return render(request, signin_template)
    else:
        return render(request, signup_template)


def signin(request):
    signin_template = 'signin.html'
    if request.POST:
        data = request.POST
        user = authenticate(username=data.get("email"), password=data.get("password"))
        if user:
            login(request, user)
            messages.add_message(request, messages.SUCCESS, 'Successfully Login.')
            return redirect('/home')
        else:
            messages.add_message(request, messages.ERROR, 'Username or Password Incorrect.')
            return redirect('/signin')
    else:
        return render(request, signin_template)


@login_required
def logout_view(request):
    logout(request)
    return redirect("/")


@login_required
def home(request):
    connection = MongoDBUtil.get_conn()
    db = connection[config.MONGO_DB_NAME]
    collection = db['jobs']
    required_condition = {'status': 'ACTIVE'}
    if not request.user.is_superuser:
        required_condition.update({'user_id': str(request.user.id)})
    jobs = list(collection.find(required_condition))
    logger.info("jobs: " + str(jobs))
    collection = db['contacts']
    required_condition = {'status': 'ACTIVE'}
    contacts = list(collection.find(required_condition))
    logger.info("contacts: " + str(contacts))
    return render(request, 'home.html', {"jobs": jobs, "contacts": contacts})


@login_required
def new_job(request):
    data = request.POST
    connection = MongoDBUtil.get_conn()
    db = connection[config.MONGO_DB_NAME]
    collection = db['jobs']
    total_jobs = len(list(collection.find({})))
    body = {'job_id': total_jobs + 1,
            "name": data.get("new_job_name"),
            "website_url": data.get("website_url"),
            "user_id": str(request.user.id),
            "status": 'ACTIVE'}
    jobs = list(collection.find({'user_id': str(request.user.id), 'status': 'ACTIVE'}))
    job_names = [job["name"].lower() for job in jobs]
    if body.get("name").lower() in job_names:
        messages.add_message(request, messages.ERROR, 'Job name already present. Please choose different job name.')
    else:
        logger.info("create new job." + str(body))
        collection.insert_one(body)
    jobs = list(collection.find({'user_id': str(request.user.id), 'status': 'ACTIVE'}))
    logger.info("jobs: " + str(jobs))
    return render(request, 'home.html', {"jobs": jobs})


@login_required
def delete_job(request):
    data = request.POST
    connection = MongoDBUtil.get_conn()
    db = connection[config.MONGO_DB_NAME]
    collection = db['jobs']
    collection.update_one({'user_id': str(request.user.id), 'job_id': int(data.get("job_id")), "status": 'ACTIVE'},
                          {'$set': {'status': 'INACTIVE'}}, upsert=True)
    required_condition = {'status': 'ACTIVE'}
    if not request.user.is_superuser:
        required_condition.update({'user_id': str(request.user.id)})
    jobs = list(collection.find(required_condition))
    collection = db["contacts"]
    contacts = list(collection.find({"status": "ACTIVE"}))
    logger.info("jobs: " + str(jobs))
    logger.info("contacts: " + str(contacts))
    return render(request, 'home.html', {"jobs": jobs, "contacts": contacts})


@login_required
def mark_as_read(request):
    data = request.POST
    connection = MongoDBUtil.get_conn()
    db = connection[config.MONGO_DB_NAME]
    collection = db['contacts']
    collection.update_one({'contact_id': int(data.get("contact_id")), "status": 'ACTIVE'},
                          {'$set': {'status': 'INACTIVE'}}, upsert=True)
    required_condition = {'status': 'ACTIVE'}
    if not request.user.is_superuser:
        required_condition.update({'user_id': str(request.user.id)})
    collection = db["jobs"]
    jobs = list(collection.find(required_condition))
    collection = db["contacts"]
    contacts = list(collection.find({"status": "ACTIVE"}))
    logger.info("jobs: " + str(jobs))
    logger.info("contacts: " + str(contacts))
    return render(request, 'home.html', {"jobs": jobs, "contacts": contacts})


def new_contact(request):
    data = request.POST
    if data.get("full_name") in constant.IGNORE_CONTACT:
        return redirect("/")
    connection = MongoDBUtil.get_conn()
    db = connection[config.MONGO_DB_NAME]
    collection = db['contacts']
    total_jobs = len(list(collection.find({})))
    body = {'contact_id': total_jobs + 1,
            "full_name": data.get("full_name"),
            "email": data.get("email"),
            "phone": data.get("phone"),
            "message": data.get("message"),
            "status": 'ACTIVE'
            }
    collection.insert_one(body)
    return redirect("/")


@login_required
def runspider(request):
    data = request.POST
    schedule_job_url = 'http://127.0.0.1:6800/schedule.json'
    if request.POST and data.get("spider_name"):
        scrapyd_job = requests.post(schedule_job_url,
                                    data={'project': 'default', 'spider': request.POST.get('spider_name')})
        job_info = json.loads(scrapyd_job.content)
        if scrapyd_job.status_code == constant.HTTP_OK:
            return download(request, job_info, str(job_info.get("jobid")), data.get("spider_name"))
        else:
            messages.add_message(request, messages.WARNING,
                                 'Error in running the Spider. Please contact admin sonrajbrijesh@gmail.com')
            return redirect("/home")
    elif request.POST and not data.get("spider_name"):
        messages.add_message(request, messages.WARNING,
                             'Spider is not attached yet. Please contact admin sonrajbrijesh@gmail.com')
        return redirect("/home")
    else:
        return redirect("/home")


def download(request, job_info, path, spider_name):
    scrapy_list_jobs = 'http://localhost:6800/listjobs.json'
    while True:
        scrapy_list_job = requests.get(scrapy_list_jobs, data={'project': 'default'})
        finished_jobs = [job.get("id") for job in json.loads(scrapy_list_job.content).get("finished")]
        if job_info.get("jobid") in finished_jobs:
            file_path = os.path.join(settings.BASE_DIR, "output/" + path)
            if os.path.exists(file_path):
                with open(file_path, 'rb') as fh:
                    response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
                    response['Content-Disposition'] = 'inline; filename=' + spider_name + '.csv'
                    return response
            else:
                messages.add_message(request, messages.WARNING,
                                     'Error running in the Spider. Please contact admin sonrajbrijesh@gmail.com')
                return redirect("/home")
        time.sleep(1)


def pricing(request):
    return render(request, 'pricing.html')


def about(request):
    return render(request, 'about.html')


def contact(request):
    return render(request, 'contact.html')


@login_required
def subscription(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price': 'price_1MaYAYSIC5v4grMxXSIulYqz',
            'quantity': 1,
        }],
        mode='payment',
        success_url=request.build_absolute_uri(reverse('thanks')) + '?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=request.build_absolute_uri(reverse('subscription')),
    )
    context = {
        'session_id': session.id,
        'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY,
    }
    return render(request, 'subscription.html', context)


def thanks(request):
    return render(request, 'thanks.html')


@login_required
def query(request):
    template = 'query.html'
    return render(request, template)


@login_required
def quick(request):
    template = 'quick.html'
    return render(request, template)