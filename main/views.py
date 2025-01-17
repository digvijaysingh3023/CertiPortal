from turtle import pos
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from .models import *
from .render import Render
from .forms import *
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib import messages
from .choices import *
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, EmailValidator
from post_office import mail
import os
from django.http import HttpResponse
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q

# Create your views here.
def index(request):
    return render(request , 'registration/index.html')

def logoutView(request):
    logout(request)
    return render(request , 'registration/logout.html')

def certificateNotFound(request):
    return render(request , 'main/certificateNotFound.html')

def certificate(request, cert_id):
    try:
        candid = candidate.objects.get(certificate_url=cert_id)
        print(candid.certificate_type)
    except candidate.DoesNotExist:
        candid = None

    if not candid or not candid.is_valid:
        # DO SOMETHING 
        return redirect('certificateNotFound')

    context = {
        'candid_name' : candid.name,
        'candid_event' : candid.event,
        'candid_position': candid.position,
        'candid_college' : candid.college,
        'candid_achievement' : candid.special_achievement,
    }
    print(candid.certificate_type)
    if candid.event == 'Parliamentry Debate':
        return Render.render('certificate/certificatePD.html',context)
    elif candid.certificate_type == 'SA':
        return Render.render('certificate/certificateSA.html',context)
    elif candid.certificate_type == 'P': 
        return render(request, 'certificate/certificateParticipation.html', context)

    elif candid.certificate_type == 'CA_P': 
        return render(request, 'certificate/certificateCAPlat.html', context)
    elif candid.certificate_type == 'CA_G': 
        return render(request, 'certificate/certificateCAGold.html', context)
    elif candid.certificate_type == 'CA_S': 
        return render(request, 'certificate/certificateCASilver.html', context)
    elif candid.certificate_type == 'CA_Part': 
        return render(request, 'certificate/certificateCAPart.html', context)

    elif candid.certificate_type == 'W': 
        return render(request, 'certificate/certificateWinner.html', context)
    elif candid.certificate_type == 'R1': 
        return render(request, 'certificate/certificateFirstRunner.html', context)
    elif candid.certificate_type == 'R2': 
        return render(request, 'certificate/certificateSecondRunner.html', context)
    elif candid.certificate_type == 'R':
        return render(request, 'certificate/certificaterunner.html', context)
    elif candid.certificate_type == 'MP':
        return render('certificate/certificateManshaktiParticipant.html',context)
    elif candid.certificate_type == 'MW':
        return Render.render('certificate/certificateManshaktiWinner.html',context)
   


def isDuplicate(alcher_id, event, certificate_type, year):
    try:
        candid = candidate.objects.get(alcher_id=alcher_id, event=event, 
            certificate_type=certificate_type, year=year)
    except candidate.DoesNotExist:
        return False
    else:
        return True
    

def generateUrl(email , year):
    last_num = 0
    # candid_certificates = candidate.objects.filter(email=email).order_by('-pk')
    # if len(candid_certificates) > 0:  
    #     latest_cert = candid_certificates.first()
    #     arr = latest_cert.certificate_url.split('-')
    #     last_num = int(arr[4])
    new_url = email + '-' + str(year) + '-' + str(last_num+1) + '-' + os.urandom(8).hex()
    return new_url


@login_required
def candidForm(request):
    if request.method == 'POST':
        form = CandidForm(request.POST)
        if form.is_valid():
            alcher_id = form.cleaned_data['alcher_id']
            name = form.cleaned_data['name']
            event = form.cleaned_data['event']
            certificate_type = form.cleaned_data['certificate_type']
            position = form.cleaned_data['position']
            college = form.cleaned_data['college']
            year = form.cleaned_data['year']
            email = form.cleaned_data['email']
            special_achievement = form.cleaned_data['special_achievement']
            if not isDuplicate(alcher_id, event, certificate_type, year):
                new_url = generateUrl(email , year)
                candidate.objects.create(alcher_id=alcher_id, name=name, event=event, 
                    certificate_type=certificate_type, position=position, college=college, is_valid=True, is_generated=True, 
                    certificate_url=new_url, email=email, year=year, special_achievement = special_achievement, )
            return redirect('candidList')
    else:
        form = CandidForm()
    
    return render(request, 'main/candidform.html', {'form':form} ) 

@login_required
def candidList(request):
    # candids = candidate.objects.filter(year=current_year()-1)     #for previous year ex: 2020
    candids = candidate.objects.filter(year=current_year())   #for current year ex: 2021
    event_name='none'
    context = {
        'candids': candids,
        'event_name': event_name,
    }
    print("Now the candids data will be printed")
    print(candids)
    return render(request, 'main/candidlist.html', context)


@login_required
def delete_candidate(request, certificate_url):
    candid = candidate.objects.filter(certificate_url=certificate_url).first()
    candid.delete()
    return redirect('candidList')

@login_required
def send_email(request , alcher_id, certificate_url):
    print("here")
    try:
        candid = candidate.objects.get(alcher_id = alcher_id, certificate_url = certificate_url)
    except candidate.DoesNotExist:
        candid = None

    if not candid or not candid.is_valid:
        #Candidate does not exist return to index.html
        return render(request, 'registration/index.html')

    context = {
        'candid' : candid
    }

    if candid.event == 'Parliamentry Debate':
        content = render_to_string('main/emails/mailPD.html', context)
    elif candid.certificate_type == 'CA_G' or  candid.certificate_type == 'CA_P' or  candid.certificate_type == 'CA_S' or candid.certificate_type == 'CA_Part':
        # html_message = render_to_string('main/emails/mailca.html', context)
        # content = strip_tags(html_message)
        content = render_to_string('main/emails/mailca.html', context)
    elif candid.certificate_type == 'P':
        content = render_to_string('main/emails/mailparticipant.html', context)
    elif candid.certificate_type == 'W' or candid.certificate_type == 'R1' or candid.certificate_type == 'R2' or candid.certificate_type == 'R':
        # print(context.candid.certificate_url)
        content = render_to_string('main/emails/mailwinner.html', context)
    elif candid.certificate_type == 'SA':
        content = render_to_string('main/emails/mailsa.html', context)
    elif candid.certificate_type == 'MW':
        content = render_to_string('main/emails/mailmswinner.html', context)
    elif candid.certificate_type == 'MP':
        content = render_to_string('main/emails/mailmsparticipant.html', context)
    message = EmailMultiAlternatives(
        subject = "Alcheringa'22 Certification",
        to = [candid.email],
    )
    message.attach_alternative(content, "text/html")
    message.send(fail_silently=False)
    return render(request, 'main/mail_sent.html' , context)


@login_required
def send_email_to_all(request):
    print("here")
    candids = candidate.objects.all()

    for candid in candids:
        context = {
            'candid' : candid
        }
        if candid.event == 'Parliamentry Debate':
            content = render_to_string('main/emails/mailPD.html', context)
        elif candid.certificate_type == 'CA_G' or  candid.certificate_type == 'CA_P' or  candid.certificate_type == 'CA_S' or candid.certificate_type == 'CA_Part':
            # html_message = render_to_string('main/emails/mailca.html', context)
            # content = strip_tags(html_message)
            content = render_to_string('main/emails/mailca.html', context)
        elif candid.certificate_type == 'P':
            content = render_to_string('main/emails/mailparticipant.html', context)
        elif candid.certificate_type == 'W' or candid.certificate_type == 'R1' or candid.certificate_type == 'R2' or candid.certificate_type == 'R':
            # print(context.candid.certificate_url)
            content = render_to_string('main/emails/mailwinner.html', context)
        elif candid.certificate_type == 'SA':
            content = render_to_string('main/emails/mailsa.html', context)
        elif candid.certificate_type == 'MW':
            content = render_to_string('main/emails/mailmswinner.html', context)
        elif candid.certificate_type == 'MP':
            content = render_to_string('main/emails/mailmsparticipant.html', context)
        message = EmailMultiAlternatives(
            subject =  "Alcheringa'22 Certification",
            to = [candid.email],
        )
        message.attach_alternative(content, "text/html")
        message.send(fail_silently=False)
    return render(request, 'main/mail_sent.html' , context)
    



def readDataFromCSV(csv_file):
    event_choices_list = [x[0] for x in EVENT_OPTIONS]
    certificate_choices_list = [x[0] for x in CERTIFICATE_OPTIONS]
    file_data = csv_file.read().decode("utf-8") 
    lines = file_data.split("\n")
    
    skipped_candids = []
    for line in lines:
        fields = line.split(",")
        if len(fields) < 5:
            continue

        alcher_id = fields[0].strip()        
        name = fields[1].strip()
        certificate_type = fields[2].strip()  
        position = fields[3].strip()
        
        college = fields[4].strip()
        event = fields[5].strip()
        year = fields[6].strip()
        email = fields[7].strip()

        # print(alcher_id, name, certificate_type, position, college, event, year, email)

        try:
            if position:
                position = int(position)
            else:
                position = 1
            email_validator = EmailValidator()
            alcher_id_validator = RegexValidator(r"ALC-[0-9]{4}-[0-9A-Za-z]+")
            alcher_id_validator(alcher_id)
            email_validator(email)
        except (ValidationError, ValueError) as e :
            skipped_candids.append((alcher_id,event))
            continue

        # if certificate_type not in certificate_choices_list or event not in event_choices_list:
        #     skipped_candids.append((alcher_id,event))
        #     continue

        if not isDuplicate(email, event, certificate_type, year):
            new_url = generateUrl(email, year)
            print(alcher_id, event, certificate_type, year)
            candidate(alcher_id=alcher_id, name=name, event=event, 
                    certificate_type=certificate_type, position=position, college=college, is_valid=True, is_generated=True, 
                    certificate_url=new_url, email=email, year=year).save()
    return skipped_candids


@login_required
def candidBulk(request):
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        context = {
        'form': CSVUploadForm(),
        }
        if form.is_valid():
            csv_file = request.FILES['file_CSV']
            if not csv_file.name.endswith('.csv'):
                messages.error(request,'ERROR!! File is not CSV type')
                return redirect('candidBulk')
            if csv_file.multiple_chunks():
                messages.error(request,"ERROR!! Uploaded file is too big (%.2f MB)." % (csv_file.size/(1000*1000))) 
                return redirect('candidBulk')
            skipped_candids = readDataFromCSV(csv_file)
            if len(skipped_candids)>0:
                context['skipped_candids'] = skipped_candids,
            messages.success(request, 'SUCCESS!! Data uploaded')

            return render(request, 'main/candidbulk.html', context)
        
        return HttpResponse('Hey you just made an error!')
    else:
        form = CSVUploadForm()
        return render(request, 'main/candidbulk.html', {'form':form}) 


@login_required
def candidUpdateForm(request, tpk):
    if request.method == 'POST':
        form = CandidForm(request.POST)
        if form.is_valid():
            alcher_id = form.cleaned_data['alcher_id']
            name = form.cleaned_data['name']
            event = form.cleaned_data['event']
            certificate_type = form.cleaned_data['certificate_type']
            year = form.cleaned_data['year']
            email = form.cleaned_data['email']
            is_valid = form.cleaned_data['is_valid']
            position = form.cleaned_data['position']
            college = form.cleaned_data['college']
            special_achievement = form.cleaned_data['special_achievement']

            try:
                obj = candidate.objects.get(pk=tpk)
            except:
                return redirect('candidList')

            obj.alcher_id = alcher_id
            obj.name = name
            obj.event = event
            obj.certificate_type = certificate_type
            obj.year = year
            obj.email = email
            new_url = generateUrl(email ,year)
            obj.certificate_url = new_url
            obj.is_valid = is_valid
            obj.position = position
            obj.college = college
            obj.special_achievement = special_achievement
            obj.save()
            messages.success(request, "SUCCESS!! Candidate updated successfully")
            return redirect('candidList')
    else:
        

        try:
            obj = candidate.objects.get(pk=tpk)
        except:
            obj=None
            # print(tpk,type(tpk))
            return redirect('candidList')
        # print(obj.__dict__)
        form = CandidForm(initial=obj.__dict__)
    
    return render(request, 'main/candidform.html', {'form':form}) 

def candidListFilter(request, id):
    event = EVENT_OPTIONS[id][0]
    candids = candidate.objects.filter(year=current_year(), event = event)
    context = {
        'candids': candids,
        'event_name': event,
    }
    return render(request, 'main/candidlist.html', context)



from django.core.mail import send_mass_mail

@login_required
def massmail(request,event_name):
    # if event_name == 'none':
    #     print("here")
    #     candids = candidate.objects.filter(year=current_year())
    #     context = {'candids': candids,
    #     'event_name' : 'none',}
    #     return render(request, 'main/candidlist.html', context)

    candids = candidate.objects.filter(year=current_year(), event=event_name)
    message_list = []
    
    for candid in candids:
        context = {'candid' : candid, }
        subject =  "Alcheringa'22 Certification"
        if candid.event == 'Parliamentry Debate':
            content = render_to_string('main/emails/mailPD.txt', context)
        elif candid.certificate_type == 'P':
            content = render_to_string('main/emails/mailparticipant.txt', context)
        elif candid.certificate_type == 'W':
            content = render_to_string('main/emails/mailwinner.txt', context)
        elif candid.certificate_type == 'SA':
            content = render_to_string('main/emails/mailsa.txt', context)
        elif candid.certificate_type == 'MW':
            content = render_to_string('main/emails/mailmswinner.txt', context)
        elif candid.certificate_type == 'MP':
            content = render_to_string('main/emails/mailmsparticipant.txt', context)

        sender = 'publicrelations23@alcheringa.in'
        recipient = [candid.email]
        message  = (subject, content , sender , recipient)
        message_list.append(message)
    
    message_tuple = tuple(message_list)
    send_mass_mail(message_tuple, fail_silently=False)
    candids = candidate.objects.filter(year=current_year())
    context = {
        'candids': candids,
        'event_name' : 'none'
    }
    return render(request, 'main/candidlist.html', context)





@login_required
def calist(request):
    candids = candidate.objects.filter(year=current_year(), certificate_type = 'CA_G' ) | candidate.objects.filter(year=current_year(), certificate_type = 'CA_S' ) | candidate.objects.filter(year=current_year(), certificate_type = 'CA_P' ) | candidate.objects.filter(year=current_year(), certificate_type = 'CA_Part' ) 
    context = {
        'candids': candids,
        }
    return render(request, 'main/calist.html', context)

@login_required
def massmailca(request):
    print("here")
    candids = candidate.objects.filter(Q(certificate_type = 'CA_G')|Q(certificate_type = 'CA_Part')|Q(certificate_type = 'CA_P')|Q(certificate_type = 'CA_S'))
    
    for candid in candids:
        context = {'candid' : candid, }
        content = render_to_string('main/emails/mailca.html', context)
        message = EmailMultiAlternatives(
            subject =  "Alcheringa'22 Certification",
            to = [candid.email],
        )
        message.attach_alternative(content, "text/html")
        message.send(fail_silently=False)
    
    context = {
        'candids': candids,
    }
    return render(request, 'main/calist.html', context)



@login_required
def salist(request):
    candids = candidate.objects.filter(year=current_year(), certificate_type = 'SA' )
    context = {
        'candids': candids,
        }
    return render(request, 'main/salist.html', context)


@login_required
def massmailsa(request):
    candids = candidate.objects.filter(year=current_year(), certificate_type = 'SA')
    message_list = []
    
    for candid in candids:
        context = {'candid' : candid, }
        subject =  "Alcheringa'22 Certification"
        content = render_to_string('main/emails/mailsa.txt', context)
        sender = 'publicrelations23@alcheringa.in'
        recipient = [candid.email]
        message  = (subject, content , sender , recipient)
        message_list.append(message)
    
    message_tuple = tuple(message_list)
    send_mass_mail(message_tuple, fail_silently=False)
    candids = candidate.objects.filter(year=current_year(), certificate_type = 'SA')
    context = {
        'candids': candids,
    }
    return render(request, 'main/salist.html', context)
