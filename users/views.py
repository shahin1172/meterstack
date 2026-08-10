from django.shortcuts import render
from rest_framework_simplejwt  .  views import  TokenObtainPairView
from ..users import token
from rest_framework import generics, status
from rest_framework.response import Response
from .serializers import Userregistrationserializer
from .models import User



class Userregistrationview(generics.GenericAPIView):
    queryset=User.objects.all()
    serializer_class=Userregistrationserializer



# Create your views here.
