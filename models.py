from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import backref

db = SQLAlchemy()

# models
class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contracts = db.relationship('Contract', backref=backref('patient', uselist=False), lazy=True)
    forms = db.relationship('Form', backref=backref('patient', uselist=False), lazy=True)
    medicines = db.relationship('Medicine', backref=backref('patient', uselist=False), lazy=True)
    algorithms = db.relationship('Algorithm', backref=backref('patient', uselist=False), lazy=True)

    def as_dict(self):
        return {
            "id": self.id,
            "contracts": [contract.as_dict() for contract in self.contracts],
            "forms": [form.as_dict() for form in self.forms],
            "medicines": [medicine.as_dict() for medicine in self.medicines],
            "algorithms": [algorithm.as_dict() for algorithm in self.algorithms]
        }

class Contract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id', ondelete="CASCADE"), nullable=False)
    clinic_id = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    agent_token = db.Column(db.String(255), nullable=True)

    forms = db.relationship('Form', backref=backref('contract', uselist=False), lazy=True)
    medicines = db.relationship('Medicine', backref=backref('contract', uselist=False), lazy=True)
    algorithms = db.relationship('Algorithm', backref=backref('contract', uselist=False), lazy=True)

    is_admin = db.Column(db.Boolean, default=False)

    def as_dict(self, native=False):
        serialized = {
            "id": self.id,
            "clinic_id": self.clinic_id
        }

        if native:
            serialized['agent_token'] = self.agent_token

        return serialized

class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id', ondelete="CASCADE"), nullable=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract.id', ondelete="CASCADE"), nullable=True)

    title = db.Column(db.String(255), nullable=True)
    rules = db.Column(db.Text, nullable=True)
    timetable = db.Column(db.JSON, nullable=True)
    is_template = db.Column(db.Boolean, default=False)
    template_id = db.Column(db.Integer, db.ForeignKey('medicine.id', ondelete="set null"), nullable=True)

    last_sent = db.Column(db.DateTime(), nullable=True)

    warning_days = db.Column(db.Integer, default=0)
    warning_timestamp = db.Column(db.Integer, default=0)
    filled_timestamp = db.Column(db.Integer, default=0)

    def as_dict(self):
        return {
            "id": self.id,
            "contract_id": self.contract_id,
            "patient_id": self.patient_id,
            "title": self.title,
            "rules": self.rules,
            "timetable": self.timetable,
            "is_template": self.is_template,
            "template_id": self.template_id,
            "warning_days": self.warning_days
        }

    def timetable_description(self):
        if self.timetable['mode'] == 'daily':
            return '{} раз(а) в день'.format(len(self.timetable['points']))
        elif self.timetable['mode'] == 'weekly':
            return '{} раз(а) в неделю'.format(len(self.timetable['points']))
        else:
            return '{} раз(а) в месяц'.format(len(self.timetable['points']))

    def clone(self):
        new_medicine = Medicine()
        new_medicine.title = self.title
        new_medicine.rules = self.rules

        new_medicine.timetable = self.timetable
        new_medicine.warning_days = self.warning_days

        if self.is_template:
            new_medicine.template_id = self.id
        else:
            new_medicine.template_id = self.template_id

        return new_medicine

class Form(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id', ondelete="CASCADE"), nullable=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract.id', ondelete="CASCADE"), nullable=True)

    title = db.Column(db.String(255), nullable=True)
    doctor_description = db.Column(db.Text, nullable=True)
    patient_description = db.Column(db.Text, nullable=True)
    thanks_text = db.Column(db.Text, nullable=True)

    show_button = db.Column(db.Boolean, default=False)
    button_title = db.Column(db.String(255), nullable=True)

    fields = db.Column(db.JSON, nullable=True)
    timetable = db.Column(db.JSON, nullable=True)

    is_template = db.Column(db.Boolean, default=False)
    template_id = db.Column(db.Integer, db.ForeignKey('form.id', ondelete="set null"), nullable=True)
    categories = db.Column(db.String(512), nullable=True)

    algorithm_id = db.Column(db.Integer, db.ForeignKey('algorithm.id', ondelete="set null"), nullable=True)
    clinics = db.Column(db.JSON, nullable=True)

    last_sent = db.Column(db.DateTime(), nullable=True)

    warning_days = db.Column(db.Integer, default=0)
    warning_timestamp = db.Column(db.Integer, default=0)
    filled_timestamp = db.Column(db.Integer, default=0)

    template_category = db.Column(db.String(512), default="Общее", nullable=True)
    instant_report = db.Column(db.Boolean, default=False, nullable=False, server_default='false')

    def as_dict(self):
        return {
            "id": self.id,
            "contract_id": self.contract_id,
            "patient_id": self.patient_id,
            "title": self.title,
            "doctor_description": self.doctor_description,
            "patient_description": self.patient_description,
            "thanks_text": self.thanks_text,
            "fields": self.fields,
            "timetable": self.timetable,
            "show_button": self.show_button,
            "button_title": self.button_title,
            "is_template": self.is_template,
            "template_id": self.template_id,
            "algorithm_id": self.algorithm_id,
            "warning_days": self.warning_days,
            "template_category": self.template_category,
            "instant_report": self.instant_report,
            "clinics": self.clinics
        }

    def clone(self):
        new_form = Form()
        new_form.title = self.title
        new_form.doctor_description = self.doctor_description
        new_form.patient_description = self.patient_description
        new_form.thanks_text = self.thanks_text
        new_form.show_button = self.show_button
        new_form.button_title = self.button_title
        new_form.fields = self.fields
        new_form.timetable = self.timetable
        new_form.algorithm_id = self.algorithm_id
        new_form.categories = self.categories
        new_form.warning_days = self.warning_days
        new_form.instant_report = self.instant_report


        if self.is_template:
            new_form.template_id = self.id
        else:
            new_form.template_id = self.template_id

        return new_form

class Algorithm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id', ondelete="CASCADE"), nullable=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract.id', ondelete="CASCADE"), nullable=True)

    title = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)

    # legacy
    # todo - make transition
    criteria = db.Column(db.JSON, nullable=True)
    actions = db.Column(db.JSON, nullable=True)

    # actual
    steps = db.Column(db.JSON, nullable=True)
    initial_step = db.Column(db.String(128), nullable=True)
    current_step = db.Column(db.String(128), nullable=True)
    timeout_at = db.Column(db.Integer, server_default="0")

    categories = db.Column(db.String(512), nullable=True)
    is_template = db.Column(db.Boolean, default=False)
    template_id = db.Column(db.Integer, db.ForeignKey('algorithm.id', ondelete="set null"), nullable=True)
    attached_form = db.Column(db.Integer, nullable=True)

    template_category = db.Column(db.String(512), default="Общее", nullable=True)
    clinics = db.Column(db.JSON, nullable=True)

    def as_dict(self, native=False):
        return {
            "id": self.id,
            "contract_id": self.contract_id,
            "patient_id": self.patient_id,
            "title": self.title,
            "description": self.description,
            "steps": self.steps,
            "categories": self.categories,
            "is_template": self.is_template,
            "template_id": self.template_id,
            "template_category": self.template_category,
            "attached_form": self.attached_form,
            "clinics": self.clinics
        }

    def clone(self):
        new_algorithm = Algorithm()
        new_algorithm.title = self.title
        new_algorithm.description = self.description
        new_algorithm.steps = self.steps
        new_algorithm.categories = self.categories
        new_algorithm.attached_form = self.attached_form

        if self.is_template:
            new_algorithm.template_id = self.id
        else:
            new_algorithm.template_id = self.template_id

        return new_algorithm
