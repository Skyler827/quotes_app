import re
import bcrypt
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as translate
from django.core.exceptions import ObjectDoesNotExist
import datetime

class CustomUserManager(models.Manager):
    def all_fields(self, post_data):
        errors = {}
        required_fields = ["fname", "lname", "email", "birthday", "password", "password-conf"]
        missing_fields = filter(lambda field: field not in post_data.keys(), required_fields)
        for field in missing_fields:
            errors[missing_fields] = "Request is missing a value in the field: "+field
        return errors
    def passwords_equal(self, post_data):
        errors = {}
        if post_data["password"] != post_data ["password-conf"]:
            errors["password-confirm"] = "The password and password-confirm must match"
        return errors
    def password_long_enough(self, post_data):
        errors = {}
        min_pass_length = 5
        if len(post_data["password"]) < min_pass_length:
            errors["password"] = "Password must be at least "+str(min_pass_length)+" characters."
        return errors
    def valid_email(self, post_data):
        errors = {}
        # regex source: http://emailregex.com/
        if not re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", post_data["email"]):
            errors["email"] = "Must enter a valid email address"
        return errors
    def valid_dob(self, post_data):
        errors = {}
        if datetime.datetime.strptime(post_data["birthday"], "%Y-%m-%d") > datetime.datetime.now():
            errors["birthday"] = "You must be born in the past" 
        return errors
    def registration_validator(self, post_data):
        errors = {}
        errors.update(self.passwords_equal(post_data))
        errors.update(self.password_long_enough(post_data))
        errors.update(self.valid_email(post_data))
        errors.update(self.all_fields(post_data))
        errors.update(self.valid_dob(post_data))
        return errors
    def login_validator(self, post_data):
        errors = {}
        #step 1: get a user and return if we cant find one
        user_id = None
        if "email" not in post_data:
            errors["email"] = "Request must contain a value for email"
        if "password" not in post_data:
            errors["password"] = "Request must contain a value for password"
        if all(x not in errors.keys() for x in ["email", "password"]):
            users = CustomUser.objects.filter(email=post_data["email"])
            for u in users:
                if bcrypt.checkpw(post_data["password"].encode(), u.pass_hash):
                    user_id = u.id
            if users.count() == 0:
                errors["email"] = "No user found with that email"
            if users.count() > 0 and user_id == None:
                errors["password"] = "Incorrect Password"
        return (errors, user_id)

class CustomUser(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    b_day = models.DateTimeField()
    pass_hash = models.BinaryField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()
class SpeakerManager(models.Manager):
    def validate_request(self, request_post):
        errors = []
        speaker = None
        if "name" not in request_post.keys():
            errors.append("No speaker name given")
        else: 
            n = request_post["name"]
            if len(n) == 0:
                errors.append("speaker name cannot be empty")
            elif len(n) < 4:
                errors.append("speaker name \""+n+"\"is too short, must be at least 4 characters")
            elif len(n) > 99:
                errors.append("speaker name is too long, must be under 100 characters")
        valid = len(errors) == 0
        if valid:
            speaker = Speaker.objects.create(name=n)
        return valid, errors, speaker
class Speaker(models.Model):
    name = models.CharField(max_length=100)
    objects = SpeakerManager()
class QuoteManager(models.Manager):
    def validate_request(self, request_post, request_session): 
        errors = []
        quote = None
        if len(request_post["text"]) < 10:
            errors.append("quote must be at least 10 characters")
        valid = len(errors) == 0
        if valid:
            quote = Quote.objects.create(
                uploader=CustomUser.objects.get(id=request_session["user_id"]),
                speaker=Speaker.objects.get(id=request_post["speaker"]),
                text=request_post["text"]
            )
        return valid, errors, quote
    def validate_add2favs_request(self, request, quote_id):
        errors = []
        quote = None
        if "user_id" in request.session.keys():
            try:
                u = CustomUser.objects.get(id=request.session["user_id"])
                try:
                    quote_id_n = int(quote_id)
                    quote = Quote.objects.get(id=quote_id_n)
                    u.favored_quotes.add(quote)
                except ValueError:
                    errors.append("quote ID given is not an integer")
                except ObjectDoesNotExist:
                    errors.append("No such quote with id: \""+quote_id+"\"")
            except ObjectDoesNotExist:
                errors.append("No user found with id: \""+request.session['user_id']+"\"")
        else:
            errors.append("Invalid user id")
        valid = len(errors) == 0
        return valid, errors, quote
class Quote(models.Model):
    uploader = models.ForeignKey(CustomUser, related_name="uploaded_quotes")
    speaker = models.ForeignKey(Speaker, related_name="quotes")
    favoring_users = models.ManyToManyField(CustomUser, related_name="favored_quotes")
    text = models.TextField()
    objects = QuoteManager()