import PyPDF2
import docx
import json
import openai
import os
from flask import Flask, render_template, request, jsonify, send_file

openai.api_key = '******'

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

requirements = {
    "location": "Tel Aviv",
    "language": "English","hebrew"
    "experience": "3 years",
    "salary_range": (20000, 22000),
    "skills": ["Python", "SQL","java"],
    "education": "University student"
}


requirement_scores = {key: 1 for key in requirements}
question_index = 0
max_questions = 4


class App:

    def __init__(self):
        self.app = Flask(__name__)
        self.setup_routes()
        self.dic_data = {}
        self.keys_list = []
        self.resume_content = None
        self.current_question = "תודה על הרצון שלך לעבוד איתנו, נשמח שתספר לנו קצת על עצמך:)"
        self.AI_questions = ["תודה על הרצון שלך לעבוד איתנו, נשמח שתספר לנו קצת על עצמך:)"]
        self.requirements = requirements
        self.counter_question = 1
        self.checkt = []
        self.backround_data = {}
        self.user_answers = []
        self.Flage = True
        self.last_subject = ""

    def extract_text_from_pdf(self, file_path):
        text = ""
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text()
        return text

    def extract_text_from_docx(self, file_path):
        doc = docx.Document(file_path)
        return " ".join([paragraph.text for paragraph in doc.paragraphs])

    def get_missing_requirements(self, text_cv):
        prompt = f"""Task Definition: Analyze the provided text CV and determine which of the following requirements can be identified from it and fit the requirements of an employer listed below.
        Requirements to Identify:
        Location
        Language
        Experience
        Salary Range
        Skills
        Education
        Output:
        Provide a dictionary with key for each requirement and score from this option ["fail", "weak", "Suitable for the job", "Unknown"] 
        According to the compliance with the attached job requirements. For example, if one lives in London and the job is in Tel Aviv, it fails, but if one lives in Caesarea, it is weak,
        and if one lives near Tel Aviv, it is suitable.
        input requirements: {self.requirements}
        Input text: {text_cv}
        Response must be valid JSON."""

        response = openai.ChatCompletion.create(
            model='gpt-4',
            messages=[
                {"role": "user", "content": prompt},
            ]
        )
        dic_cv = json.loads(response.choices[0].message['content'])
        dic_cv = self.change_dict_keys_to_lower(dic_cv)
        self.dic_data = dic_cv
        print(self.dic_data)
        self.keys_list = [key for key, value in self.dic_data.items() if value in ["weak","fail","Unknown"]]
        return dic_cv

    def start_speak(self, current_answer):
        prompt = f"""Task Definition: Analyze the provided answer and determine the following requirements.
        Requirements to Identify:
        Location
        Language
        Experience
        Salary Range
        Skills
        Education
        Output:
        Provide a dictionary with key for each requirement and score from this option ["fail", "weak", "Suitable for the job", "Unknown"] 
        According to the compliance with the attached job requirements. For example, if one lives in London and the job is in Tel Aviv, it fails, but if one lives in Caesarea, it is weak,
        and if one lives near Tel Aviv, it is suitable.
        input requirements: {self.requirements}
        look for anderstand the contact of the question i give you also input of what we ask
        input the quisten: {self.current_question}
        Input text: {current_answer}
        
        Response must be valid JSON."""

        response = openai.ChatCompletion.create(
            model='gpt-4',
            messages=[
                {"role": "user", "content": prompt},
            ]
        )
        t = response.choices[0].message['content']
        print(t)
        try:
            dic_text = json.loads(response.choices[0].message['content'])
        except:
            raise 'something went wrong, try to send again.'
        dic_text = self.change_dict_keys_to_lower(dic_text)
        for key, value in dic_text.items():

            if value in ["weak", "fail", "Suitable for the job"]:
                self.dic_data[key] = value
                try:
                    self.keys_list.remove(key)
                except:
                    print(key)
        return self.dic_data
    def mingaline_question(self):
        prompt = f"""Task Definition: Generate a question to start a nice HR interview to get the employee feel comftorable
        Output:
        Example: "tell me about your family"
        i want the question to be in hebrew and Please use accessible and friendly language.
        """
        response = openai.ChatCompletion.create(
            model='gpt-4',
            messages=[
                {"role": "user", "content": prompt},
            ]
        )
        question = response.choices[0].message['content']
        self.current_question = question
        self.AI_questions.append(question)
        return question

    def generate_question(self, question_subject):
        prompt = f"""Task Definition: Generate a question to determine the following requirements.
        Requirements to Identify: {question_subject}
        Output:
        A question that helps you get the data to check if it fits the requirements. 
        Example: "Where do you live now?"
        i want the question to be in hebrew and Please use accessible and friendly language.
        """
        response = openai.ChatCompletion.create(
            model='gpt-4',
            messages=[
                {"role": "user", "content": prompt},
            ]
        )
        question = response.choices[0].message['content']
        self.current_question = question
        self.AI_questions.append(question)
        return question

    def generate_question_total(self):
        prompt = f"""
        Generate a question for a job candidate applying for a general position.
        The question should aim to gather initial and specific information about the candidate, for personal_topics like [
        "Communication Skills",
        "Teamwork and Collaboration",
        "Problem-Solving and Creativity",
        "Adaptability and Flexibility",
        "Work Ethic and Motivation",
        "Leadership Potential",
        "Cultural Fit",
        "Interpersonal Skills",
        "Conflict Resolution",
        "Personal Development",interpersonal skills, problem-solving, and handling pressure] 
        Avoid asking for direct facts like location or experience.
        i want the question to be in hebrew and Please use accessible and friendly language.
        """

        response = openai.ChatCompletion.create(
            model='gpt-4',
            messages=[
                {"role": "user", "content": prompt},
            ]
        )
        question = response.choices[0].message['content']
        self.current_question = question
        self.AI_questions.append(question)
        return question


    def change_dict_keys_to_lower(self, dic):
        new_dic = {}
        for key in dic.keys():
            new_dic[key.lower()] = dic[key]
        return new_dic

    def check_answer(self):
        prompt = f"""""Task Definition: Analyze the following candidate's response to an interview question.
    Based on the answer, 
    evaluate and return a dictionary with ratings between 1-5 for the following personal_topics = [
    "Communication Skills",
    "Teamwork and Collaboration",
    "Problem-Solving and Creativity",
    "Adaptability and Flexibility",
    "Work Ethic and Motivation",
    "Leadership Potential",
    "Cultural Fit",
    "Interpersonal Skills",
    "Conflict Resolution",
    "Personal Development",interpersonal skills, problem-solving, and handling pressure] 
    The ratings should reflect how well the candidate demonstrated these attributes in their response, where 1 is the lowest and 5 is the highest.
    Provide a dictionary with key for topics you understand from the question and the value is score the number 1-5 
    the question that the candidate's response: {self.AI_questions}
    Here is the candidate's response: {self.user_answers}
    Response must be valid JSON."""

        response = openai.ChatCompletion.create(
            model='gpt-4',
            messages=[
                {"role": "user", "content": prompt},
            ]
        )
        try:
            dic_text = json.loads(response.choices[0].message['content'])
        except:
            raise 'something went wrong, try to send again.'
        dic_text = self.change_dict_keys_to_lower(dic_text)
        for key, value in dic_text.items():
            self.backround_data[key] = value
        print(self.backround_data)

        return self.backround_data

    def _index(self):
        global question_index, requirement_scores
        question_index = 0
        self.user_answers.clear()
        requirement_scores = {key: 1 for key in requirements}
        return render_template('index.html')

    def _upload(self):
        if 'resume' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        file = request.files['resume']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        self.resume_content = file_path
        if file.filename.endswith('.pdf'):
            resume_text = self.extract_text_from_pdf(file_path)
        elif file.filename.endswith('.docx'):
            resume_text = self.extract_text_from_docx(file_path)
        else:
            return jsonify({'error': 'Unsupported file type'}), 400

        dic_data = self.get_missing_requirements(resume_text)
        self.dic_data = dic_data
        first_question = "תודה על הרצון שלך לעבוד איתנו, נשמח שתספר לנו קצת על עצמך:)"
        return jsonify({'success': True, 'first_question': first_question}), 200

    def _ask(self):
        global question_index

        user_input = request.form['question']
        self.user_answers.append(user_input)
        if self.Flage:
            self.dic_data = self.start_speak(user_input)
        # self.backround_data = self.check_answer(user_answers)
        filtered_list = [item for item in self.keys_list if item not in self.checkt]
        self.keys_list = filtered_list
        if self.counter_question < 3:
            next_question = self.mingaline_question()
            self.counter_question += 1
            return jsonify({'answer': next_question, 'end': False})
        elif self.keys_list:

            if self.last_subject == self.keys_list[0]:
                # jsonify({'answer': "נא תרשום תשובה רלוונטית", 'end': False}
                self.checkt.append(self.keys_list[0])
            next_question = self.generate_question(self.keys_list[0])
            self.last_subject = self.keys_list[0]
            self.counter_question += 1
            return jsonify({'answer': next_question, 'end': False})
        elif self.counter_question < 8:
            self.Flage = False
            next_question = self.generate_question_total()
            self.counter_question += 1
            return jsonify({'answer': next_question, 'end': False})
        else:
            self.backround_data = self.check_answer()
            print(self.backround_data)
            return jsonify({'answer': 'The interview is over. You can view the report now.', 'end': True})

    def _report(self):
        report_data = {
            "requirements": self.dic_data,
            "conversation": list(zip(self.AI_questions[:len(self.user_answers)], self.user_answers)),
            "feedback": self.backround_data
        }
        return render_template('report.html', report=report_data, resume_content=self.resume_content)

    def setup_routes(self):
        @self.app.route('/report', methods=['GET'])
        def create_report():
            return self._report()

        @self.app.route('/ask', methods=['POST'])
        def ask():
            return self._ask()

        @self.app.route('/upload', methods=['POST'])
        def upload():
            return self._upload()

        @self.app.route('/')
        def index():
            return self._index()

        @self.app.route('/download_resume', methods=['GET', 'POST'])
        def download():
            return send_file(
                self.resume_content,
                download_name='resume.pdf',
                as_attachment=True
            )


if __name__ == '__main__':
    app_cls = App()
    app_cls.app.run(debug=True)
