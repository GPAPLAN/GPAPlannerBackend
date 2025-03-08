from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from .models import User, Note, gpa
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from googleapiclient.discovery import build
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask import current_app
from . import email_utils
from flask_mail import Message
import os
from datetime import datetime


auth = Blueprint('auth', __name__)




@auth.route('/reset-password', methods=['GET','POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form.get('email')
        provided_answer = request.form.get('security-answer', '')
        new_password = request.form.get('new-password', '')


        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.security_answer, provided_answer):
            user.password = generate_password_hash(new_password)
            db.session.commit()
            flash("Password reset has been successful", category='success')
            return redirect(url_for('auth.login'))
        else:
            flash("incorrect security answer", category='error')
            return render_template('reset_password_request.html')
    return render_template('reset_password_request.html')
    

@auth.route('/landing')
def landing_page():
    return render_template("index.html")




@auth.route('/request-reset', methods=['GET','POST'])
def request_reset():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            return render_template('reset_password_request.html', email=email, security_question=user.security_question)
        else:
            flash('no account found with that email address', category='error')
            return render_template("getEmail.html")
    return render_template("getEmail.html")




@auth.route('/get-security-question')
def get_security_question():
    email = request.args.get('email')
    user = User.query.filter_by(email=email).first()
    if user:
        return jsonify(security_question=user.security_question)
    else:
        return jsonify(error='user not found'), 404    






@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method =='POST':
        email = request.form.get('email', '')
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password): # type: ignore
                flash("successfully logged in!", category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('email does not exist,', category='error')
    
    return render_template("login.html", user=current_user )

@auth.route('/calendar')
@login_required
def calendar():
    return render_template('calendar.html')




@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template('index.html')


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method =='POST':
        email = request.form.get('email')
        first_name=request.form.get('first_name')
        last_name =request.form.get('last_name')
        password1= request.form.get('password1')
        password2= request.form.get('password2')
        security_question = request.form.get('security-question')
        security_answer = request.form.get('security-answer')

        

        user = User.query.filter_by(email=email).first()

        if user:
            flash('email already exists', category='error')
        elif email is not None and len(email) < 4:
            flash('email must be more than 3 characters.', category='error')
        elif first_name is not None and len(first_name) < 2:
            flash('first name must be more than 1 characters.', category='error')
        elif password1 != password2:
            flash('password doesnt match ', category='error')
        elif password1 is not None and len(password1) < 7:
            flash('password must be more than 7 characters.', category='error')
        else:
            
            new_user = User(email=email, first_name=first_name, last_name=last_name, security_question=security_question, security_answer=security_answer,password=generate_password_hash(password1, method='pbkdf2:sha256')) # type: ignore
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('you successfully created your account!!!!', category='success')
            return redirect(url_for('views.home'))

    return render_template("signup.html", user=current_user)

@auth.route('/info_page')
def info_page():
    return render_template('info_page.html', user=current_user)


@auth.route('/account', methods=['GET', 'POST'])
def account():
    user_gpa = gpa.query.filter_by(user_id=current_user.id).first()
    if user_gpa:
        goal_gpa = user_gpa.goal_gpa
        current_gpa=user_gpa.current_gpa
        completed_credits=user_gpa.completed_credits
        remaining_credits=user_gpa.remaining_credits
        required_gpa = user_gpa.required_gpa
    else:
        goal_gpa = None
        current_gpa= None
        completed_credits=0
        remaining_credits=0
        return render_template("account.html", user=current_user, goal_gpa='not set', current_gpa='not set', remaining_credits='not set', completed_credits='not set', required_gpa='n/a', required_grade_message='not available, do calculation on gpa planner')

        
    if remaining_credits > 0:
        required_gpa = calculate_required_gpa(current_gpa, completed_credits, goal_gpa, remaining_credits)
        grade_message = required_grade_message(required_gpa)
    else:
        required_gpa ='n/a'
        grade_message = 'not applicable'

    return render_template("account.html", user=current_user, goal_gpa=goal_gpa, current_gpa=current_gpa, remaining_credits=remaining_credits, completed_credits=completed_credits, required_gpa=required_gpa, required_grade_message=grade_message)




@auth.route('/program', methods=['GET', 'POST'])
def program():
    if request.method =='POST':
        try:
            current_gpa = float(request.form['current_gpa'])
            completed_credits = int(request.form['completed_credits'])
            goal_gpa = float(request.form['goal_gpa'])
            remaining_credits = int(request.form['remaining_credits'])
        except ValueError:
            flash('please enter all fields correctly. Fields cannot be left blank.', category='error')
            return redirect(url_for('auth.program'))
        
        if 0 in [current_gpa, completed_credits, goal_gpa, remaining_credits]:
            flash('All values must be valid and not zero', category='error')
            return redirect(url_for('auth.program'))
        
    
        gpa_info = gpa.query.filter_by(user_id=current_user.id).first()

    
    
        if gpa_info:
            gpa_info.current_gpa = current_gpa
            gpa_info.goal_gpa = goal_gpa
            gpa_info.completed_credits = completed_credits
            gpa_info.remaining_credits = remaining_credits
        else:
            new_gpa = gpa(
                current_gpa=current_gpa,
                goal_gpa=goal_gpa,
                completed_credits=completed_credits,
                remaining_credits=remaining_credits,
                
                user_id=current_user.id
            ) # type: ignore
            db.session.add(new_gpa)
        db.session.commit()

        required_gpa = calculate_required_gpa(current_gpa, completed_credits, goal_gpa, remaining_credits)
        required_gpa =float(required_gpa)
        message = required_grade_message(required_gpa)

        return render_template('result.html', 
                               message = message,
                               current_gpa=current_gpa, 
                               goal_gpa=goal_gpa,
                                 completed_credits=completed_credits,
                                 remaining_credits=remaining_credits, 
                                 required_gpa=required_gpa, 
                                 required_grade_message='message based on required gpa',
                                 highest_possible_gpa=min(4.0, required_gpa))
    return render_template("program.html")
    
    
    


def calculate_required_gpa(current_gpa, completed_credits, goal_gpa, remaining_credits):
    if remaining_credits <=0:
        return 'n/a'
    else:
        total_quality_points_needed = goal_gpa * (completed_credits + remaining_credits)
        current_quality_points = current_gpa * completed_credits
        required_quality_points = total_quality_points_needed - current_quality_points
        required_gpa = required_quality_points / remaining_credits
        required_gpa = float(f"{required_gpa:.3g}")

        return required_gpa

def required_grade_message(required_gpa):
    
    if required_gpa > 4.0:
        
        return f"you need a {required_gpa}/4 average grade .Reaching your GPA goal is not possible with your remaining courses"
    
    gpa_to_grade = {
        (4.0,4.0): 'You would need to get all As for the remainder of your total college courses',
        (3.7,3.99): 'You would need to get all A- s for the remainder of your total college courses ',
        (3.3,3.69): 'You would need to get all B+ for the remainder of your total college courses ',
        (3.0,3.29): 'You would need to get all Bs for the remainder of your total college courses',
        (2.7,2.99): 'You would need to get all B- for the remainder of your total college courses',
        (2.3,2.69): 'You would need to get all C+ for the remainder of your total college courses',
        (2.0,2.29): 'You would need to get all Cs for the remainder of your total college courses',
        (1.7,1.99): 'You would need to get all C- for the remainder of your total college courses',
        (1.3,1.69): 'You would need to get all D+ for the remainder of your total college courses',
        (1.0,1.29): 'You would need to get all Ds for the remainder of your total college courses',
        (0.7,0.99): 'You would need to get all D- for the remainder of your total college courses',
        (0.0,0.69): 'You would need to get all Fs for the remainder of your total college courses',
    }

    for (lower, upper), message in gpa_to_grade.items():
        if lower <= required_gpa <= upper:
            return message
        
    return '::The average grade needed to reach Your GPA goal cannot be reached::'
    
#----------------------------- v---------------------------------------------------

def calculate_tgrade():
    num_grades = int(input("How many grades do you want to calculate (up to 6)? "))
    if num_grades < 1 or num_grades > 6:
        print("Please enter a number between 1 and 6.")
        return

    total_weight = 0
    weighted_sum = 0

    for i in range(num_grades):
        grade = float(input(f"Enter grade {i+1} (%): "))
        weight = float(input(f"Enter weight for grade {i+1}: "))
        weighted_sum += grade * weight
        total_weight += weight

    if total_weight == 0:
        print("Total weight cannot be zero.")
        return

    final_grade = weighted_sum / total_weight
    print(f"\nYour final grade percentage is: {final_grade:.2f}%")

    # Determine letter grade
    if final_grade >= 97:
        letter_grade = 'A+'
    elif final_grade >= 93:
        letter_grade = 'A'
    elif final_grade >= 90:
        letter_grade = 'A-'
    elif final_grade >= 87:
        letter_grade = 'B+'
    elif final_grade >= 83:
        letter_grade = 'B'
    elif final_grade >= 80:
        letter_grade = 'B-'
    elif final_grade >= 77:
        letter_grade = 'C+'
    elif final_grade >= 73:
        letter_grade = 'C'
    elif final_grade >= 70:
        letter_grade = 'C-'
    elif final_grade >= 67:
        letter_grade = 'D+'
    elif final_grade >= 63:
        letter_grade = 'D'
    elif final_grade >= 60:
        letter_grade = 'D-'
    else:
        letter_grade = 'F'

    print(f"Your final letter grade is: {letter_grade}")
    

def calculate_grade(grades):
    total_score = 0
    total_weight = 0
    for grade, weight in grades:
        total_score += grade * weight
        total_weight += weight
    if total_weight == 0:
        return "N/A"
    else:
        return total_score / total_weight

#-----------------------------------------^-------------------------------------------------

@auth.route('/feedback',methods=['GET', 'POST'])
@login_required
def feedback():
    if request.method == 'POST':
        feedback_content = request.form.get('feedback')
        sender_email = current_user.email
        if send_feedback_email(sender_email, feedback_content): # type: ignore
            flash('thanks for feedback', category='success')
        else:
            flash('failed to send, try again later', category='error')
        return redirect(url_for('auth.feedback'))
    return render_template('feedback.html')


@auth.route('/rapidtable', methods=['GET', 'POST'])
def rapidtable():
    if request.method == "POST":
        grades = []
        for i in range(1, 7):
            grade = request.form.get(f'grade{i}', '')
            weight = request.form.get(f'weight{i}', '')
            if grade and weight:
                grades.append((float(grade), float(weight)))
        if  grades:
            final_grade = calculate_grade(grades)
            return render_template('classResults.html', final_grade=final_grade)
    return render_template("rapidtable.html")


@auth.route('/notes', methods=['GET', 'POST'])
@login_required
def notes():
    if request.method =='POST':
        note_content = request.form.get('content')
        if not note_content:
            flash('note cant be empty', category='error')
        else:
            new_note = Note(content=note_content, user_id=current_user.id)
            db.session.add(new_note)
            db.session.commit()
            flash('your note has been added!', category='success')
            return redirect(url_for('auth.notes'))
    user_notes = Note.query.filter_by(user_id=current_user.id).all()
    return render_template('notes.html', notes=user_notes)
    
    
@auth.route('/delete_note/<int:note_id>', methods=['POST'])
@login_required
def delete_note(note_id):
    note = Note.query.get(note_id)
    if note:
        db.session.delete(note)
        db.session.commit()
        flash('your note has been deleted', category='success')
    else:
        flash('note not found', category='error')
    return redirect(url_for('auth.notes'))




YOUTUBE_API_KEY = 'AIzaSyCOPEvtCVfy36Vp-eFb2BqwA1By9YBflyg'


def youtube_search(q, max_results=10, order='relevance', token=None, location=None, location_radius=None):
    school_work_keywords = ['lecture', 'tutorial', 'study', 'course', 'class']
    q += ' ' + ' '.join(school_work_keywords)
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

    search_response = youtube.search().list(
        q=q,
        type='video',
        pageToken=token,
        order=order,
        part='id,snippet',
        maxResults=max_results,
        location=location,
        locationRadius=location_radius, 
        videoCategoryId='27'
    ).execute()


    videos = []

    for search_result in search_response.get('items',[]):
        videos.append({
            'title': search_result['snippet']['title'],
            'id': search_result['id']['videoId']
        })

    return videos

@auth.route('/search', methods=['GET', 'POST'])
def search_videos():
    if request.method =='POST':
        query = request.form.get('query')
        videos = youtube_search(query)
        for video in videos:
            print(video['title'])
        return render_template('search.html', videos=videos)
    return render_template('search_form.html')







