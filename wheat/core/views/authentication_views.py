from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm

def signup(request):
    """Handle user signup, creates a request for admin approval."""
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            
            user.is_active = False
            user.save()

            return redirect("pending_approval")
    else:
        form = UserCreationForm()

    return render(request, "registration/signup.html", {"form": form})

def logged_out(request):
    """Simple logged-out confirmation page."""
    return render(request, "registration/logged_out.html")

def pending_approval(request):
    """Simple pending approval page following a signup."""
    return render(request, "registration/pending_approval.html")