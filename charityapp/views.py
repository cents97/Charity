from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect
from .forms import ContactForm
from .models import ContactMessage
from .models import HelpingHand,CharityEvent,BlogPost,Testimonial, CharityGallery
from .forms import VolunteerForm, PartnershipApplicationForm
from django.contrib import messages
from datetime import datetime
from dateutil.parser import parse
from django.utils import timezone  # Import timezone for handling timezones
import logging
import requests
from django.core.cache import cache



def home(request):
    hands = HelpingHand.objects.all()  # Get all HelpingHand objects
    events = CharityEvent.objects.order_by('date')  # Fetch events sorted by date
    blogs = BlogPost.objects.all()  # Get all blog objects

    # Create a range of stars based on the rating
    testimonials = Testimonial.objects.all()
    for testimonial in testimonials:
        testimonial.stars = range(1, testimonial.rating + 1)  # Pass a range for stars

    return render(request, 'home.html', {
        'hands': hands,
        'events': events,
        'blogs': blogs,
        'testimonials': testimonials
    })


def about(request):
    return render(request, 'about.html')

def programs(request):
    return render(request, 'programs.html')

def get_involved(request):
    return render(request, 'get_involved.html')


def events(request):
    events = CharityEvent.objects.order_by('date')  # Fetch events sorted by date
    return render(request, 'event.html', {        
        'events': events,        
    })
    
def gallery(request):
    images = CharityGallery.objects.all()
    return render(request, 'gallery.html', {'images': images})

def contact(request):
    return render(request, 'contact.html')


# Views for 'What We Do' sub-sections
def educational_support(request):
    return render(request, 'what_we_do/educational_support.html')

def spiritual_guidance(request):
    return render(request, 'what_we_do/spiritual_guidance.html')

def health_wellness(request):
    return render(request, 'what_we_do/health_wellness.html')

def moral_development(request):
    return render(request, 'what_we_do/moral_development.html')

def community_outreach(request):
    return render(request, 'what_we_do/community_outreach.html')

def emergency_relief(request):
    return render(request, 'what_we_do/emergency_relief.html')


# CHARITY

def get_involved(request):
    return render(request, 'charity/get_involved.html')

def donate(request):
    return render(request, 'charity/donate.html')




def fundraise(request):
    return render(request, 'charity/fundraise.html')

def gifts(request):
    return render(request, 'charity/gifts.html')

def contact(request):
    success_message = None
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Get form data
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']

            # Save the contact form submission to the database
            ContactMessage.objects.create(name=name, email=email, message=message)

            # Set the success message to trigger the alert
            success_message = "Your message has been sent successfully. Thank you!"

    else:
        form = ContactForm()

    return render(request, 'contact.html', {'form': form, 'success_message': success_message})

def volunteer_view(request):
    form = VolunteerForm()
    if request.method == "POST":
        form = VolunteerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your application has been submitted successfully!")
            form = VolunteerForm()  # Reset form after successful save

    return render(request, "charity/volunteer.html", {"form": form})

def partnership(request):
    if request.method == "POST":
        form = PartnershipApplicationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Thank you for your interest! We’ll get back to you soon.")
            return redirect('partnership')  # Redirect to clear form data
    else:
        form = PartnershipApplicationForm()  # Ensure a fresh form

    return render(request, "charity/partnership.html", {"form": form})



# Set up logger
logger = logging.getLogger(__name__)

# =========================== GET ACCESS TOKEN =========================== #
def get_access_token():
    """Fetches and caches the Pesapal access token"""
    # Try to get the token from cache first
    token = cache.get("pesapal_access_token")

    # If token exists in cache, return it
    if token:
        return token

    # URL to get the access token
    url = "https://cybqa.pesapal.com/pesapalv3/api/Auth/RequestToken"

    # Set the headers for the request
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # The request body with your Pesapal credentials
    data = {
        "consumer_key": settings.PESAPAL_CONSUMER_KEY,
        "consumer_secret": settings.PESAPAL_CONSUMER_SECRET
    }

    try:
        # Send the POST request to get the token
        response = requests.post(url, headers=headers, json=data)

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the response JSON
            token_data = response.json()

            # Get the token and expiry date
            new_token = token_data.get("token")
            expiry_date = token_data.get("expiryDate")

            if new_token:
                # If token is present, cache it with expiry time
                # Calculate expiration time based on expiryDate (use the expiryDate in UTC)
                cache.set("pesapal_access_token", new_token, timeout=calculate_timeout(expiry_date))

                return new_token
            else:
                logger.error("Pesapal token response missing 'token' key: %s", token_data)
                return None
        else:
            # Log if the request failed
            logger.error("Failed to get Pesapal access token. Response: %s", response.text)
            return None
    except Exception as e:
        # Log any errors that occurred during the request
        logger.error("Error occurred while requesting Pesapal token: %s", str(e))
        return None

def calculate_timeout(expiry_date):
    """Calculate the timeout for the cached token based on expiryDate."""
    # Parse the expiryDate from the API response
    expiry_datetime = parse(expiry_date)
    current_time = datetime.utcnow()

    # Calculate the time difference in seconds
    time_diff = (expiry_datetime - current_time).total_seconds()
    return max(time_diff, 0)  # Ensure timeout is not negative


def calculate_timeout(expiry_date):
    """Calculate the timeout for the cached token based on expiryDate."""
    # Parse the expiryDate from the API response (this will be an aware datetime)
    expiry_datetime = parse(expiry_date)

    # Get the current time with timezone info
    current_time = timezone.now()  # Use timezone-aware datetime

    # Calculate the time difference in seconds
    time_diff = (expiry_datetime - current_time).total_seconds()

    # Ensure timeout is not negative (if the token has expired)
    return max(time_diff, 0)



def test_pesapal_token(request):
    """Test if the Pesapal access token function is working."""
    token = get_access_token()
    if token:
        return JsonResponse({"status": "success", "token": token})
    else:
        return JsonResponse({"status": "error", "message": "Failed to retrieve token"})
