import time
from datetime import datetime, timedelta

from helpers import log
from managers.Manager import Manager
from models import Patient, Contract, Reminder


class ReminderManager(Manager):
    def __init__(self, *args):
        super(ReminderManager, self).__init__(*args)

    def get_templates(self):
        return Reminder.query.filter_by(is_template=True).all()

    def get(self, reminder_id):
        reminder = Reminder.query.filter_by(id=reminder_id).first()

        if not reminder:
            raise Exception("No reminder_id = {} found".format(reminder_id))

        return reminder

    def clear(self, contract):
        Reminder.query.filter_by(contract_id=contract.id).delete()
        self.__commit__()
        return True

    def remove(self, id, contract):
        reminder = Reminder.query.filter_by(id=id).first_or_404()

        if reminder.contract_id != contract.id and not contract.is_admin:
            return None

        reminder.canceled_at = datetime.now()

        self.__commit__()
        return id

    def set_state(self, reminder, state):

        reminder.state = state
        self.__commit__()

        patient_text = ""
        doctor_text = ""
        action = None
        if state == 'done':
            action = 'выполнил назначение'
        elif state == 'reject':
            action = 'отказался от выполнения назначения'
        elif state == 'cancel':
            action = 'отключил напоминание'

        if reminder.type == 'patient':
            patient_text = 'Спасибо! Мы сообщили врачу.'
            doctor_text = 'Пациент {}:\n\n{}'.format(action, reminder.text)
        else:
            doctor_text = 'Спасибо!'

        deadline = (datetime.now() + timedelta(days=1)).timestamp()

        if state == 'later':
            result = self.medsenger_api.send_message(reminder.contract_id, 'Напоминание автоматически отправится позже.',
                                                     only_patient=reminder.type == 'patient', only_doctor=reminder.type == 'doctor',
                                                     action_deadline=deadline)
            return result

        reminder.canceled_at = datetime.now()
        self.__commit__()

        if patient_text:
            result = self.medsenger_api.send_message(reminder.contract_id, patient_text, only_patient=True, action_deadline=deadline)
        if doctor_text:
            result = self.medsenger_api.send_message(reminder.contract_id, doctor_text, only_doctor=True, action_deadline=deadline)

        return result

    def set_next_date(self, id, contract, type, count):
        reminder = Reminder.query.filter_by(id=id).first_or_404()

        if reminder.contract_id != contract.id and not contract.is_admin:
            return None

        send_next = None

        if type == 'hour':
            send_next = datetime.now() + timedelta(hours=count)
        elif type == 'day':
            send_next = datetime.now() + timedelta(days=count)

        reminder.send_next = send_next
        reminder.state = 'later'

        self.__commit__()
        return reminder.id

    def create_or_edit(self, data, contract):
        try:
            reminder_id = data.get('id')
            if not reminder_id:
                reminder = Reminder()
            else:
                reminder = Reminder.query.filter_by(id=reminder_id).first_or_404()
                if reminder.contract_id != contract.id and not contract.is_admin:
                    return None

            reminder.type = data.get('type')
            reminder.text = data.get('text')

            reminder.attach_date = data.get('attach_date')
            reminder.detach_date = data.get('detach_date')
            reminder.timetable = data.get('timetable')

            reminder.state = data.get('state', 'active')

            if data.get('is_template'):
                reminder.is_template = True
            else:
                reminder.patient_id = contract.patient_id
                reminder.contract_id = contract.id

            if not reminder_id:
                self.db.session.add(reminder)
            self.__commit__()

            return reminder
        except Exception as e:
            log(e)
            return None

    def log_request(self, reminder, contract_id=None, description=None):
        if not contract_id:
            contract_id = reminder.contract_id
        if not description:
            description = ''
            if reminder.type == 'patient':
                description += "Отправка напоминания пациенту: \"{}\". ".format(reminder.text)
            if reminder.type == 'patient' or reminder.type == 'both':
                description += "Отправка напоминания врачу: \"{}\".".format(reminder.text)

        super().log_request("reminder_{}".format(reminder.id), contract_id, description)

    def run(self, reminder, commit=True):
        result = None
        if reminder.type == 'patient':
            result = self.medsenger_api.send_message(reminder.contract_id, reminder.text, action_name='Отметить действие',
                                                     action_onetime=True, action_big=False,
                                                     action_link='reminder/{}'.format(reminder.id), only_patient=True)
        if reminder.type == 'doctor':
            result = self.medsenger_api.send_message(reminder.contract_id, reminder.text, action_name='Отметить действие',
                                                     action_onetime=True, action_big=False,
                                                     action_link='reminder/{}'.format(reminder.id), only_doctor=True)
        if result:
            reminder.last_sent = datetime.now()
            if commit:
                self.__commit__()
                return result

        return result
