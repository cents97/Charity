from django.shortcuts import render
import requests
import re
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect
from .forms import ContactForm
from .models import ContactMessage
from .models import HelpingHand,CharityEvent,BlogPost,Testimonial, CharityGallery
from .forms import VolunteerForm, PartnershipApplicationForm
from django.contrib import messages

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

def donate(request):
    return render(request, 'donate.html')

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

def process_payment(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        phone_number = request.POST.get("phone_number")
        amount = request.POST.get("amount")
        payment_method = request.POST.get("payment_method")

        # Validate phone number format (should be in 2567XXXXXXXX format)
        if not re.match(r"^2567\d{8}$", phone_number):
            return JsonResponse({"error": "Invalid phone number format. Use 2567XXXXXXXX."}, status=400)

        # Flutterwave API URL
        url = "https://api.flutterwave.com/v3/payments"
        
        headers = {
            "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
            "Content-Type": "application/json",
        }
        
        data = {
            "tx_ref": "donation_" + str(amount),  # Unique transaction ID
            "amount": amount,
            "currency": "UGX",
            "payment_options": payment_method,
            "redirect_url": "https://yourwebsite.com/payment-success",
            "customer": {
                "email": email,
                "name": name,
                "phone_number": phone_number,
            },
            "customizations": {
                "title": "St. Thadeous Charity Donation",
                "description": "Thank you for your support!",
            },
        }

        # Send request to Flutterwave
        response = requests.post(url, json=data, headers=headers)
        res_data = response.json()

        # Redirect user to payment link
        if res_data["status"] == "success":
            return redirect(res_data["data"]["link"])
        else:
            return JsonResponse({"error": "Payment Failed"}, status=400)

    return render(request, "charity/payment.html")
