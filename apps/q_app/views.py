import datetime
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import CustomUser, Quote, Speaker
import bcrypt

min_password_length = 4

def index(request):
    request.session._get_or_create_session_key()
    if "user_id" in request.session.keys():
        user_id = request.session["user_id"]
        u = CustomUser.objects.filter(id=user_id)
        if u:
            return redirect("/quotes")
    return render(request, "lr_app/index.jinja2")
def hash(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())
def register(request):
    errors = CustomUser.objects.registration_validator(request.POST)
    if len(errors) < 10:
        bd = request.POST["birthday"]
        bd_datetime = datetime.datetime(
            year = int(bd[0:4]),
            month = int(bd[5:7]),
            day = int(bd[8:10])
        )
        print(bd_datetime)
        CustomUser.objects.create(
            first_name=request.POST["fname"],
            last_name=request.POST["lname"],
            email=request.POST["email"],
            b_day=bd_datetime,
            pass_hash=hash(request.POST["password"])
        )
    return redirect("/")
def login(request):
    errors, u_id = CustomUser.objects.login_validator(request.POST)
    for k, v in errors.items():
        messages.add_message(request, messages.ERROR, k+": "+v)
    if u_id:
        request.session["user_id"] = u_id
    if len(errors) == 0:
        messages.add_message(request, messages.INFO, "Login succesful")
    return redirect("/")
def quotes_index(request):
    if "user_id" in request.session.keys():
        u = CustomUser.objects.filter(id=request.session["user_id"]).first()
        if u:
            return render(
                request,
                "q_app/quotes_index.jinja2",
                {
                    "new_speaker": False,
                    "user":u,
                    "users": CustomUser.objects.all(),
                    "speakers": Speaker.objects.all(),
                    "non_favorites": filter(
                        lambda quote: u not in quote.favoring_users.all(),
                        Quote.objects.all()
                    )
                }
            )
    return redirect("/")

def quotes_new_speaker(request):
    if "user_id" in request.session.keys():
        u = CustomUser.objects.filter(id=request.session["user_id"]).first()
        if u:
            return render(
                request,
                "q_app/quotes_index.jinja2",
                {
                    "new_speaker": True,
                    "user":u,
                    "users": CustomUser.objects.all(),
                    "non_favorites": filter(
                        lambda quote: u not in quote.favoring_users.all(),
                        Quote.objects.all()
                    )
                }
            )
    return redirect("/")
def add_speaker(request):
    valid, errors, speaker = Speaker.objects.validate_request(request.POST)
    if valid:
        messages.add_message(request, messages.INFO, f"Added new speaker \"{speaker.name}\"")
    else:
        for e in errors:
            messages.add_message(request, messages.ERROR, e)
    return redirect("/quotes")
def add_quote(request):
    valid, errors, quote = Quote.objects.validate_request(request.POST, request.session)
    if valid:
        messages.add_message(request, messages.INFO, f"Added new quote by \"{quote.speaker.name}\"")
    else:
        for e in errors:
            messages.add_message(request, messages.ERROR, e)
    return redirect("/quotes")
def add_quote_to_favs(request, quote_id):
    valid, errors, quote = Quote.objects.validate_add2favs_request(request, quote_id)
    if valid:
        messages.add_message(request, messages.INFO, f"Added new quote by \"{quote.speaker.name}\" to your favorites")
    else:
        for e in errors:
            messages.add_message(request, messages.ERROR, e)
    return redirect("/quotes")
def remove_quote_from_favs(request, quote_id):
    u = CustomUser.objects.get(id=request.session["user_id"])
    try:
        u.favored_quotes.remove(Quote.objects.get(id=int(quote_id)))
        messages.add_message(request, messages.INFO, "removed quote from your favorites")
    except:
        messages.add_message(request, messages.ERROR, "could not remove quote from favorites")
    return redirect("/quotes")
def quotes_uploaded_by(request, user_id):
    target_user = CustomUser.objects.get(id=user_id)
    return render(request, "q_app/quotes_uploaded_by.jinja2", {
        "subject_user": CustomUser.objects.get(id=request.session["user_id"]),
        "target_user" : target_user,
        "quotes": target_user.uploaded_quotes.all(),
        "count": target_user.uploaded_quotes.count()

    })
def quotes_spoken_by(request, speaker_id):
    return render(request, "q_app/quotes_spoken_by.jinja2", {
        "speaker": Speaker.objects.get(id=speaker_id),
        "user": CustomUser.objects.get(id=request.session["user_id"]),
        "quotes": Speaker.objects.get(id=speaker_id).quotes.all(),
        "count": Speaker.objects.get(id=speaker_id).quotes.count()
    })
def logout(request):
    del request.session["user_id"]
    return redirect("/")
