from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.contrib.auth.forms import AuthenticationForm
from .forms import *
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate
from django.contrib.auth import login as login_default
from django.views import generic
from django.test import RequestFactory
from .models import Event
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from pyzbar.pyzbar import decode
import numpy as np
import uuid
import cv2
import base64
import json
import qrcode
from datetime import datetime
from django.db.models import Q


######################################################################## Login Views
def index(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("qualafesta:login"))
    user = request.user
    try:
        customer = Customer.objects.get(user_id=user)
        return HttpResponseRedirect(
            reverse('qualafesta:customer'))
    except: pass
    try:
        organizer = Organizer.objects.get(user_id=user)
        return HttpResponseRedirect(
            reverse('qualafesta:organizer'))
    except: pass
    try:
        acess_controller = AcessController.objects.get(user_id=user)
        return HttpResponseRedirect(
            reverse('qualafesta:acess_controller'))
    except: pass
    if request.user.is_superuser:
        return redirect('/admin/')
    return render(request, 'index.html', {})

def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login_default(request, user)
            context={'user':user}
        try:
            customer = Customer.objects.get(user_id=user)
            return HttpResponseRedirect(
                reverse('qualafesta:customer'))
        except: pass
        try:
            organizer = Organizer.objects.get(user_id=user)
            return HttpResponseRedirect(
                reverse('qualafesta:organizer'))
        except: pass
        try:
            acess_controller = AcessController.objects.get(user_id=user)
            return HttpResponseRedirect(
                reverse('qualafesta:acess_controller'))
        except: pass
        if request.user.is_superuser:
            return redirect('/admin/')
    
    form = CustomAuthenticationForm()
    context = {'form': form}
    return render(request, 'user_controll/login.html', context)

def register(request):
    return render(request, 'user_controll/register.html', {})

def user_register(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password1']
        user_kwargs ={
            'first_name': first_name,
            'last_name': last_name,
            'username': username,
            'email': email,
            'password': password
        }
        user = User.objects.create_user(**user_kwargs)
        return user

def register_customer(request):
    if request.method == 'POST':
        user = user_register(request)
        phone = request.POST['phone']
        profile_image = None
        try:
            profile_image = request.FILES['profile_image']
            if profile_image:
                original_name = profile_image.name
                unique_name = f"{uuid.uuid4().hex}_{original_name}"
                profile_image.name = unique_name
        except:
            pass
        if user:
            login_default(request,user)
            user.save()
            group = Group.objects.get(name='Customers')
            group.user_set.add(user)
            customer_kwargs = {
                'user_id': user,
                'phone': phone,
                'profile_image':profile_image
            }
            customer = Customer.objects.create(**customer_kwargs)
            customer.save()
            return HttpResponseRedirect(
                reverse('qualafesta:customer'))
    else:
        form = CustomerRegistrationForm()
    context = {'form': form, 'type_user':'customer'}
    return render(request, 'user_controll/register.html', context)

def register_organizer(request):
    if request.method == 'POST':
        user = user_register(request)
        phone = request.POST['phone']
        profile_image = None
        cnpj = request.POST['cnpj']
        try:
            profile_image = request.FILES['profile_image']
            if profile_image:
                original_name = profile_image.name
                unique_name = f"{uuid.uuid4().hex}_{original_name}"
                profile_image.name = unique_name
        except:
            pass
        if user:
            login_default(request,user)
            user.save()
            group = Group.objects.get(name='Organizers')
            group.user_set.add(user)
            organizer_kwargs = {
                'user_id': user,
                'phone': phone,
                'profile_image':profile_image,
                'cnpj':cnpj
            }
            organizer = Organizer.objects.create(**organizer_kwargs)
            organizer.save()
            return HttpResponseRedirect(
                reverse('qualafesta:organizer'))
    else:
        form = OrganizerRegistrationForm()
    context = {'form': form, 'type_user':'organizer'}
    return render(request, 'user_controll/register.html', context)

def register_acess_controller(request):
    if request.method == 'POST':
        user = user_register(request)
        phone = request.POST['phone']
        profile_image = None
        organization = request.POST['organization']
        try:
            profile_image = request.FILES['profile_image']
            if profile_image:
                original_name = profile_image.name
                unique_name = f"{uuid.uuid4().hex}_{original_name}"
                profile_image.name = unique_name
        except:
            pass
        if user:
            login_default(request,user)
            user.save()
            group = Group.objects.get(name='AcessControllers')
            group.user_set.add(user)
            acess_controller_kwargs = {
                'user_id': user,
                'phone': phone,
                'profile_image':profile_image,
                'organization':organization
            }
            acess_controller = AcessController.objects.create(**acess_controller_kwargs)
            acess_controller.save()
            return HttpResponseRedirect(
                reverse('qualafesta:acess_controller'))
    else:
        form = AcessControllerRegistrationForm()
    context = {'form': form, 'type_user':'acess_controller'}
    return render(request, 'user_controll/register.html', context)


######################################################################## Customer Views
def is_customer(user):
    return user.groups.filter(name='Customers').exists()

@login_required
@user_passes_test(is_customer)
def customer_index(request):
    return render(request, 'customer/customer_index.html', {})

class EventAboutView(generic.DetailView):
    model = Event
    template_name = 'customer/customer_eventAbout.html'

class EventAttractionsView(generic.DetailView):
    model = Event
    template_name = 'customer/customer_eventAttractions.html'

def TicketsListViews(request):
    ticketsorder = TicketsOrder.objects.filter(customer_id=request.user.id)
    user_instance = get_object_or_404(Customer, user_id=request.user.id)
    return render(request, 'customer/customer_ticketsList.html', {'ticketsorder': ticketsorder, 'user_instance':user_instance})

def generate_qr_code(request, text):
    # Create a QR code instance
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=0,
    )
    qr.add_data(text)
    qr.make(fit=True)

    # Create an image from the QR code instance
    img = qr.make_image(fill_color="black", back_color="white")

    # Response with the image content
    response = HttpResponse(content_type="image/png")
    img.save(response, "PNG")
    return response


######################################################################## Organizer Views
def is_organizer(user):
    return user.groups.filter(name='Organizers').exists()

@login_required
@user_passes_test(is_organizer)
def organizer_index(request):
    user_instance = get_object_or_404(Organizer, user_id=request.user.id)
    return render(request, 'organizer/organizer_index.html', {"user_instance":user_instance})

def organizer_events(request):
    user_instance = get_object_or_404(Organizer, user_id=request.user.id)
    return render(request, 'organizer/organizer_events.html', {"user_instance":user_instance})


######################################################################## Acesss Controller Views
def is_acess_controller(user):
    return user.groups.filter(name='AcessControllers').exists()

@login_required
@user_passes_test(is_acess_controller)
@csrf_exempt
def search_event_controller(request):
    try:
        context = {}
        search = request.GET['search_event_controller']
        events = Event.objects.filter(Q(name__icontains=search) | Q(description__icontains=search))
        if len(events)>0:
            context['event_list'] = events
            context['search_message'] = f'Resultados para a busca de "{search}"'
            return render(request, 'acess_controller/acess_controller_index.html', context)
        else:
            context['error_message'] = f'Nenhum evento encontrado para a busca "{search}"'
            print(context)
            return render(request, 'acess_controller/search_event_controller.html', context)
    except:
        return render(request, 'acess_controller/search_event_controller.html', {})
      
class EventControllerViews(generic.ListView):
    model = Event
    template_name = 'acess_controller/acess_controller_index.html'

class EventControllView(generic.DetailView):
    model = Event
    template_name = 'acess_controller/controll_event.html'

def get_ticket_data(ticket_hash, event_id):
    try:
        purchased_ticket = PurchasedTicket.objects.get(hash_code=ticket_hash)
        ticket_order = purchased_ticket.ticket_order_id
        user = ticket_order.customer_id 
        customer = Customer.objects.get(user_id=user.id)
        context ={
            'ticket_hash': ticket_hash,
            'event_id': event_id,
            'first_name':user.first_name,
            'last_name':user.last_name,
            'profile_image': customer.profile_image,
            'user':user,
            'correct':True,
        }
        if purchased_ticket.status:
            context['correct'] = False
            context['error_message'] ='Este ingresso já foi validado'
        elif ticket_order.payment_situation != 0:
            context['correct'] = False
            context['error_message'] ='O pagamento deste ingresso não foi efetuado'
    except:
        context ={
            'ticket_hash': ticket_hash,
            'event_id': event_id,
            'correct':False,
            'error_message':'Ingresso não encontrado'
        }
    return context

@login_required
@user_passes_test(is_acess_controller)
@csrf_exempt
def ticket_detail(request, pk):
    ticket_hash = request.GET['query']
    context = get_ticket_data(ticket_hash, pk)
    return render(request, 'acess_controller/ticket_data.html', context)

@login_required
@user_passes_test(is_acess_controller)
@csrf_exempt
def validate_ticket(request, event_id, ticket_hash):
    purchased_ticket = PurchasedTicket.objects.get(hash_code=ticket_hash)
    controller_user = request.user
    purchased_ticket.acess_controller_id = controller_user
    purchased_ticket.status = True
    purchased_ticket.entrance = datetime.now()
    purchased_ticket.save()
    return redirect(f'/acess_controller/controll_event{str(event_id)}')

@login_required
@user_passes_test(is_acess_controller)
@csrf_exempt
def scan_qr(request):
    if request.method == 'POST':
        received_data = json.loads(request.body)
        event_id = received_data.get('event_id')
        image_data = received_data.get('image')
        image_data = base64.b64decode(image_data.split(',')[1])
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        decoded_objects = decode(gray_img)
        if decoded_objects:
            qr_data = decoded_objects[0].data.decode('utf-8')
            redirect_url = f'ticket_detail?query={qr_data}'
            return JsonResponse({'message': 'QR code decodificado com sucesso', 
                                 'redirect_url': redirect_url,
                                 'hash_code': qr_data})
        else:
            return JsonResponse({'message': 'Nenhum QR code encontrado', 
                                 'redirect_url':None,'hash_code':None})
    else:
        return JsonResponse({'error': 'Invalid request method'})