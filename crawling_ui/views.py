import os
import json
import time
import subprocess
import uuid
from datetime import datetime

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
    logger.info("Rendering index page")
    template = 'index.html'
    return render(request, template)


def signup(request):
    logger.info("Processing signup request")
    signup_template = 'signup.html'
    signin_template = 'signin.html'
    if request.POST:
        data = request.POST
        logger.info(f"Signup attempt with email: {data.get('email')}")
        user = User.objects.filter(email=data.get("email"))
        if user:
            logger.info(f"User with email {data.get('email')} already exists, redirecting to signin")
            return render(request, signin_template)
        else:
            logger.info(f"Creating new user with email {data.get('email')}")
            user = User.objects.create_user(
                first_name=data.get("firstname"),
                last_name=data.get("lastname"),
                username=data.get("email"),
                email=data.get("email"),
                password=data.get("password")
            )
            user.save()
            # create new user with the credit 5
            connection = MongoDBUtil.get_conn()
            db = connection[config.MONGO_DB_NAME]
            collection = db['users']
            body = {'user_id': user.id, 'credit': 5}
            collection.insert_one(body)
            logger.info(f"User {user.id} created successfully with 5 credits")
            login(request, user)
            request.POST = {"new_job_name": 'Test Job',
                            "website_url": 'https://webscraper.io/test-sites',
                            'spider_name': 'TestSpider'
                            }
            logger.info("Creating default test job for new user")
            new_job(request)
            return redirect('/home')
    else:
        return render(request, signup_template)


def signin(request):
    logger.info("Processing signin request")
    signin_template = 'signin.html'
    if request.POST:
        data = request.POST
        logger.info(f"Login attempt with email: {data.get('email')}")
        user = authenticate(username=data.get("email"), password=data.get("password"))
        if user:
            login(request, user)
            logger.info(f"User {user.id} logged in successfully")
            messages.add_message(request, messages.SUCCESS, 'Successfully Login.')
            return redirect('/home')
        else:
            logger.info(f"Failed login attempt for email: {data.get('email')}")
            messages.add_message(request, messages.ERROR, 'Username or Password Incorrect.')
            return redirect('/signin')
    else:
        return render(request, signin_template)


@login_required
def logout_view(request):
    logger.info(f"User {request.user.id} logged out")
    logout(request)
    return redirect("index")


@login_required
def home(request):
    # jobs
    connection = MongoDBUtil.get_conn()
    db = connection[config.MONGO_DB_NAME]
    collection = db['jobs']
    required_condition = {'status': 'ACTIVE'}
    if not request.user.is_superuser:
        required_condition.update({'user_id': str(request.user.id)})
    jobs = list(collection.find(required_condition))
    logger.info("jobs: " + str(jobs))
    # contacts
    collection = db['contacts']
    required_condition = {'status': 'ACTIVE'}
    contacts = list(collection.find(required_condition))
    logger.info("contacts: " + str(contacts))
    # user info
    collection = db['users']
    required_condition = {'user_id': request.user.id}
    django_user = list(collection.find(required_condition))[0] if list(collection.find(required_condition)) else []
    logger.info("User: " + str(django_user))
    return render(request, 'home.html', {"jobs": jobs, "contacts": contacts, "django_user": django_user})


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
    if data.get("spider_name"):
        body.update({'spider_name': data.get('spider_name')})
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
    logger.info(f"Deleting job ID: {data.get('job_id')} for user {request.user.id}")
    connection = MongoDBUtil.get_conn()
    db = connection[config.MONGO_DB_NAME]
    collection = db['jobs']
    collection.update_one({'user_id': str(request.user.id), 'job_id': int(data.get("job_id")), "status": 'ACTIVE'},
                          {'$set': {'status': 'INACTIVE'}}, upsert=True)
    logger.info(f"Job ID: {data.get('job_id')} marked as INACTIVE")
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
    logger.info(f"Marking contact message ID: {data.get('contact_id')} as read")
    connection = MongoDBUtil.get_conn()
    db = connection[config.MONGO_DB_NAME]
    collection = db['contacts']
    collection.update_one({'contact_id': int(data.get("contact_id")), "status": 'ACTIVE'},
                          {'$set': {'status': 'INACTIVE'}}, upsert=True)
    logger.info(f"Contact ID: {data.get('contact_id')} marked as INACTIVE")
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
    logger.info(f"New contact message from: {data.get('full_name')} <{data.get('email')}>")
    if data.get("full_name") in constant.IGNORE_CONTACT:
        logger.info(f"Contact from {data.get('full_name')} ignored - in IGNORE_CONTACT list")
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
    logger.info(f"Contact message saved with ID: {total_jobs + 1}")
    return redirect("/")


@login_required
def runspider(request):
    data = request.POST
    logger.info(f"Running spider: {data.get('spider_name')} for user {request.user.id}")
    schedule_job_url = 'http://127.0.0.1:6800/schedule.json'
    connection = MongoDBUtil.get_conn()
    db = connection[config.MONGO_DB_NAME]
    jobs_collection = db['jobs']
    spider_info = list(jobs_collection.find({'spider_name': request.POST.get('spider_name'),
                                        'user_id': str(request.user.id)})) if not request.user.is_superuser else True
    logger.info(f"Spider info found: {spider_info}")
    user_collection = db['users']
    credit = list(user_collection.find({'user_id': request.user.id}))[0].get('credit') if list(user_collection.find({'user_id': request.user.id})) else 1 if request.user.is_superuser else 0
    logger.info(f"User {request.user.id} has {credit} credits remaining")
    if request.POST and spider_info and credit:
        logger.info(f"Scheduling spider job: {data.get('spider_name')}")
        
        # First try Scrapyd
        try:
            scrapyd_job = requests.post(schedule_job_url,
                                        data={'project': 'default', 'spider': request.POST.get('spider_name')})
            job_info = json.loads(scrapyd_job.content)
            
            if scrapyd_job.status_code == constant.HTTP_OK and job_info.get("status") == "ok":
                user_collection.update_one({'user_id': request.user.id}, {'$set': {'credit': credit - 1}})
                logger.info(f"Spider job scheduled successfully with job ID: {job_info.get('jobid')}")
                logger.info(f"Deducted 1 credit from user {request.user.id}, new balance: {credit - 1}")
                return download(request, job_info, str(job_info.get("jobid")), data.get("spider_name"))
            else:
                raise Exception(f"Scrapyd error: {job_info.get('message', 'Unknown error')}")
                
        except Exception as e:
            logger.warning(f"Scrapyd failed: {e}. Falling back to direct execution.")
            
            # Fallback to direct execution
            job_id = str(uuid.uuid4()).replace('-', '')[:16]  # Generate unique job ID
            logger.info(f"Running spider {data.get('spider_name')} directly with job ID: {job_id}")
            
            job_info = run_spider_directly(data.get('spider_name'), job_id)
            
            if job_info.get("status") == "ok":
                user_collection.update_one({'user_id': request.user.id}, {'$set': {'credit': credit - 1}})
                logger.info(f"Direct spider execution completed successfully")
                logger.info(f"Deducted 1 credit from user {request.user.id}, new balance: {credit - 1}")
                return download_direct(request, job_info, job_id, data.get("spider_name"))
            else:
                logger.error(f"Direct spider execution failed: {job_info.get('message')}")
                messages.add_message(request, messages.WARNING,
                                     'Error running spider. Please contact admin.')
                return redirect("/home")
    elif not credit:
        logger.info(f"User {request.user.id} attempted to run spider without sufficient credits")
        messages.add_message(request, messages.WARNING,
                             'Buy more credits. Please Contact Admin.')
        return redirect("/home")
    elif request.POST and not data.get("spider_name"):
        logger.info(f"User {request.user.id} attempted to run spider without specifying spider name")
        messages.add_message(request, messages.WARNING,
                             'Spider is not attached yet. Please Contact Admin.')
        return redirect("/home")
    else:
        return redirect("/home")


def download(request, job_info, path, spider_name):
    logger.info(f"Waiting for spider job {job_info.get('jobid')} ({spider_name}) to complete")
    scrapy_list_jobs = 'http://localhost:6800/listjobs.json'
    max_wait_time = 300  # 5 minutes timeout
    start_time = time.time()
    
    while True:
        # Check if we've exceeded the timeout
        if time.time() - start_time > max_wait_time:
            logger.error(f"Job {job_info.get('jobid')} ({spider_name}) timed out after {max_wait_time} seconds")
            messages.add_message(request, messages.WARNING,
                                 'Spider job timed out. Please try again or contact admin.')
            return redirect("/home")
        
        try:
            scrapy_list_job = requests.get(scrapy_list_jobs, data={'project': 'default'}, timeout=10)
            job_data = json.loads(scrapy_list_job.content)
            finished_jobs = [job.get("id") for job in job_data.get("finished", [])]
            
            if job_info.get("jobid") in finished_jobs:
                logger.info(f"Job {job_info.get('jobid')} ({spider_name}) completed, preparing download")
                
                # Try several possible file path combinations
                possible_paths = [
                    os.path.join(settings.BASE_DIR, "output", path),
                    os.path.join(settings.BASE_DIR, "output", path + ".csv"),
                    os.path.join(settings.BASE_DIR, "output", path + ".xlsx"),
                    os.path.join(settings.BASE_DIR, "output", spider_name),
                    os.path.join(settings.BASE_DIR, "output", spider_name + ".csv"),
                    os.path.join(settings.BASE_DIR, "output", spider_name + ".xlsx"),
                ]
                
                # Log all possible paths for debugging
                logger.info(f"Checking possible output file paths for spider {spider_name} with job ID {path}:")
                for p in possible_paths:
                    logger.info(f"Checking path: {p}, exists: {os.path.exists(p)}")
                
                # Ensure output directory exists
                output_dir = os.path.join(settings.BASE_DIR, "output")
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                    logger.info(f"Created missing output directory: {output_dir}")
                
                # Find the first path that exists
                for file_path in possible_paths:
                    if os.path.exists(file_path):
                        logger.info(f"Found output file at: {file_path}")
                        with open(file_path, 'rb') as fh:
                            # Determine content type based on file extension
                            content_type = "application/vnd.ms-excel"
                            if file_path.endswith('.csv'):
                                content_type = "text/csv"
                            
                            # Use the appropriate filename extension
                            filename = spider_name + ('.csv' if not file_path.endswith('.xlsx') else '.xlsx')
                            
                            response = HttpResponse(fh.read(), content_type=content_type)
                            response['Content-Disposition'] = f'inline; filename={filename}'
                            return response
                
                # If we get here, none of the possible paths existed
                # Check directory to see what's actually there
                try:
                    output_dir_contents = os.listdir(output_dir)
                    logger.error(f"Output directory contents: {output_dir_contents}")
                except Exception as e:
                    logger.error(f"Error listing output directory: {e}")
                
                messages.add_message(request, messages.WARNING,
                                    'Spider completed but output file not found. Please contact admin.')
                return redirect("/home")
        except requests.RequestException as e:
            logger.error(f"Error checking job status: {e}")
            messages.add_message(request, messages.WARNING,
                                 'Error checking spider status. Please try again.')
            return redirect("/home")
        except Exception as e:
            logger.error(f"Unexpected error in download function: {e}")
            messages.add_message(request, messages.WARNING,
                                 'Unexpected error occurred. Please try again.')
            return redirect("/home")
        
        time.sleep(3)  # Wait 3 seconds to reduce polling frequency


def pricing(request):
    logger.info("Rendering pricing page")
    return render(request, 'pricing.html')


def about(request):
    logger.info("Rendering about page")
    return render(request, 'about.html')

@login_required
def quick(request):
    logger.info(f"User {request.user.id} accessed quick page")
    template = 'quick.html'
    return render(request, template)


def contact(request):
    logger.info("Rendering contact page")
    return render(request, 'contact.html')


@login_required
def subscription(request):
    logger.info(f"User {request.user.id} accessed subscription page")
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
    logger.info(f"Created Stripe checkout session: {session.id}")
    context = {
        'session_id': session.id,
        'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY,
    }
    return render(request, 'subscription.html', context)


def thanks(request):
    session_id = request.GET.get('session_id')
    logger.info(f"Payment successful, session ID: {session_id}")
    return render(request, 'thanks.html')


@login_required
def query(request):
    logger.info(f"User {request.user.id} accessed query page")
    template = 'query.html'
    return render(request, template)

def dashboard(request):
    logger.info("Rendering dashboard page")
    return render(request, 'dashboard.html')


def run_spider_directly(spider_name, job_id):
    """
    Run spider directly using subprocess when Scrapyd is not available
    """
    try:
        # Import the file utils here to avoid circular imports
        from core.file_utils import ensure_output_directory, save_data_to_files
        
        # Make sure output directory exists
        output_dir = ensure_output_directory(settings.BASE_DIR)
        
        # Set environment variables for the spider
        env = os.environ.copy()
        env['SCRAPY_JOB'] = job_id
        
        # Run spider using subprocess with full path to scrapy executable
        # Use shell=True to ensure paths are properly resolved on Windows
        cmd = f'scrapy crawl {spider_name}'
        logger.info(f"Running spider directly with command: {cmd}")
        
        result = subprocess.run(
            cmd,
            cwd=settings.BASE_DIR,
            env=env,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            shell=True    # Use shell to ensure proper execution on Windows
        )
        
        if result.returncode == 0:
            logger.info(f"Spider {spider_name} completed successfully")
            
            # Check if output files were created
            expected_files = [
                os.path.join(output_dir, job_id + ".csv"),
                os.path.join(output_dir, job_id + ".xlsx"),
                os.path.join(output_dir, f"{spider_name}.csv"),
                os.path.join(output_dir, f"{spider_name}.xlsx"),
                os.path.join(output_dir, f"{spider_name}_backup.csv"),
                os.path.join(output_dir, f"{spider_name}_backup.json")
            ]
            
            # Check if any of the expected files exist
            files_exist = [os.path.exists(f) for f in expected_files]
            existing_files = [f for i, f in enumerate(expected_files) if files_exist[i]]
            logger.info(f"Output files exist: {existing_files}")
            
            # If no output files were found, try to create some default data
            if not any(files_exist):
                logger.warning("No output files found, creating fallback data files")
                
                # Create fallback data
                fallback_data = [
                    {
                        'Title': "Fallback data - no spider output found",
                        'Description': f"Spider {spider_name} ran successfully but did not generate output",
                        'Timestamp': datetime.now().isoformat()
                    }
                ]
                
                # Save fallback data to files
                save_data_to_files(fallback_data, job_id, settings.BASE_DIR)
                save_data_to_files(fallback_data, spider_name, settings.BASE_DIR)
            
            return {"status": "ok", "jobid": job_id}
        else:
            logger.error(f"Spider {spider_name} failed with return code {result.returncode}")
            logger.error(f"Error output: {result.stderr}")
            
            # Check error output to provide better messages
            error_data = [
                {
                    'Error': "Spider execution failed",
                    'Details': result.stderr[:500] if result.stderr else "No error details available",
                    'ReturnCode': result.returncode,
                    'Timestamp': datetime.now().isoformat()
                }
            ]
            
            # Save error data to files so we have something to return to the user
            save_data_to_files(error_data, f"{spider_name}_error", settings.BASE_DIR)
            save_data_to_files(error_data, f"{job_id}_error", settings.BASE_DIR)
            
            # Return error status but set job ID too so download function has something to look for
            return {"status": "error", "message": result.stderr, "jobid": job_id}
            
    except subprocess.TimeoutExpired:
        logger.error(f"Spider {spider_name} timed out after 5 minutes")
        
        # Create timeout data files
        timeout_data = [
            {
                'Error': "Spider execution timed out",
                'Details': f"Spider {spider_name} execution exceeded the 5-minute timeout",
                'Timestamp': datetime.now().isoformat()
            }
        ]
        save_data_to_files(timeout_data, f"{job_id}_timeout", settings.BASE_DIR)
        
        return {"status": "error", "message": "Spider execution timed out", "jobid": job_id}
    except Exception as e:
        logger.error(f"Error running spider {spider_name} directly: {e}")
        
        # Create error data files
        error_data = [
            {
                'Error': "Exception during spider execution",
                'Details': str(e),
                'Timestamp': datetime.now().isoformat()
            }
        ]
        save_data_to_files(error_data, f"{job_id}_exception", settings.BASE_DIR)
        
        return {"status": "error", "message": str(e), "jobid": job_id}

def download_direct(request, job_info, path, spider_name):
    """
    Handle download for directly executed spiders
    """
    # Import the file utils
    from core.file_utils import ensure_output_directory
    
    # Get the job ID from job_info
    job_id = job_info.get('jobid', path)
    
    # Prepare all possible filenames
    status_suffix = ""
    if job_info.get("status") != "ok":
        # If there was an error, look for error files first
        status_suffix = "_error"
        if "timed out" in job_info.get("message", "").lower():
            status_suffix = "_timeout"
        elif "exception" in job_info.get("message", "").lower():
            status_suffix = "_exception"
    
    # Ensure output directory exists
    output_dir = ensure_output_directory(settings.BASE_DIR)
    
    logger.info(f"Direct spider job {job_id} ({spider_name}) completed with status: {job_info.get('status')}, preparing download")
    
    # Try several possible file path combinations, in priority order
    possible_paths = [
        # First try the exact job_id and spider_name with any error suffix
        os.path.join(output_dir, f"{job_id}{status_suffix}.csv"),
        os.path.join(output_dir, f"{spider_name}{status_suffix}.csv"),
        os.path.join(output_dir, f"{job_id}{status_suffix}.xlsx"),
        os.path.join(output_dir, f"{spider_name}{status_suffix}.xlsx"),
        
        # Then try backup files
        os.path.join(output_dir, f"{spider_name}_backup.csv"),
        os.path.join(output_dir, f"{spider_name}_backup.json"),
        
        # Then try the original paths without any suffix
        os.path.join(output_dir, f"{job_id}.csv"),
        os.path.join(output_dir, f"{spider_name}.csv"),
        os.path.join(output_dir, f"{job_id}.xlsx"),
        os.path.join(output_dir, f"{spider_name}.xlsx"),
        
        # Raw paths without extensions
        os.path.join(output_dir, job_id),
        os.path.join(output_dir, spider_name),
        
        # Check in case paths were saved in the wrong location
        os.path.join("output", f"{job_id}.csv"),
        os.path.join("output", f"{spider_name}.csv")
    ]
    
    # Log all possible paths for debugging
    logger.info(f"Checking possible output file paths for spider {spider_name} with job ID {job_id}:")
    for p in possible_paths:
        logger.info(f"Checking path: {p}, exists: {os.path.exists(p)}")
    
    # Get a list of all files in the output directory for debugging
    try:
        dir_contents = os.listdir(output_dir)
        logger.info(f"Output directory contains {len(dir_contents)} files: {dir_contents}")
    except Exception as e:
        logger.error(f"Error listing output directory: {e}")
    
    # Find the first path that exists
    for file_path in possible_paths:
        if os.path.exists(file_path):
            logger.info(f"Found output file at: {file_path}")
            try:
                with open(file_path, 'rb') as fh:
                    # Determine content type based on file extension
                    content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"  # Default for xlsx
                    if file_path.endswith('.csv'):
                        content_type = "text/csv"
                    elif file_path.endswith('.json'):
                        content_type = "application/json"
                    
                    # Use the appropriate filename and extension
                    ext = os.path.splitext(file_path)[1] or ".csv"  # Default to .csv if no extension
                    filename = f"{spider_name}{ext}"
                    
                    response = HttpResponse(fh.read(), content_type=content_type)
                    response['Content-Disposition'] = f'inline; filename={filename}'
                    return response
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {e}")
    
    # If we get here, none of the possible paths existed or we couldn't read them
    logger.error(f"No usable output file found for spider {spider_name} with job ID {job_id}")
    
    # Generate an error file on the fly if we couldn't find any files
    try:
        error_file = os.path.join(output_dir, f"{spider_name}_error_generated.csv")
        with open(error_file, 'w', newline='') as f:
            f.write("Error,Details,Time\n")
            f.write(f"No output found,Spider ran but no output files were found,{datetime.now().isoformat()}\n")
        
        # Now serve this error file
        with open(error_file, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="text/csv")
            response['Content-Disposition'] = f'inline; filename={spider_name}_error.csv'
            return response
    except Exception as e:
        logger.error(f"Error creating error file: {e}")
        
        # Last resort - return a warning message and redirect
        messages.add_message(request, messages.WARNING,
                            'Spider completed but no output file was found or could be created. Please contact admin.')
        return redirect("/home")



