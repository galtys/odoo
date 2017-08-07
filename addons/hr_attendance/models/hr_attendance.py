# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime

from odoo import models, fields, api, exceptions, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

import base58
from bitcoin import ecdsa_sign, ecdsa_verify

#from odoo.addons.cs_signing_device.att_msg import  HrAttendanceSigned, HrAttendance
from odoo.addons.cs_signing_device.att_msg.clean_space_pb2 import  HrAttendanceSigned, HrAttendance
import hashlib

class HrAttendance(models.Model):
    _name = "hr.attendance"
    _description = "Attendance"
    _order = "check_in desc"

    def _default_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

#    employee_id = fields.Many2one('hr.employee', string="Employee", default=_default_employee, required=True, ondelete='cascade', index=True)

    employee_id = fields.Many2one('hr.employee', string="Employee")


    department_id = fields.Many2one('hr.department', string="Department", related="employee_id.department_id")
    check_in = fields.Datetime(string="Check In")
    #check_in = fields.Datetime(string="Check In", default=fields.Datetime.now, required=True)
    check_out = fields.Datetime(string="Check Out")
    worked_hours = fields.Float(string='Worked Hours', compute='_compute_worked_hours', readonly=True)
    message=fields.Text("Message")
    fingerprint_code=fields.Char("Fingerprint Code",size=444)
    task_code=fields.Char("Task Code", size=444)
    site_code=fields.Char("Site Code", size=444)
    gps=fields.Char("GPS", size=444)
    signed_msg=fields.Char("Signed Message")
    signature=fields.Text("Signature")
    site_public_key=fields.Char("Site Public Key", size=444)
    verified=fields.Boolean("VERIFIED", compute='_verified', readonly=True)

    def parse_message(self):
        for a in self:
            msg58c=a.message
            msg=base58.b58decode_check( msg58c )
            att_msg2 = HrAttendanceSigned()
            att_msg2.ParseFromString( msg )
            a.check_in=att_msg2.attendance.check_in
            a.check_out=att_msg2.attendance.check_out
            a.fingerprint_code=att_msg2.attendance.fingerprint_code
            a.task_code = att_msg2.attendance.task_code
            a.site_code = att_msg2.attendance.site_code
            a.signature = att_msg2.signature
            a.signed_msg = att_msg2.attendance.SerializeToString()

    def verify_site_and_cleaner(self):
        for a in self:
            s = self.env['project.project'].search( [('code_id.code','=',a.site_code)] )
            a.site_public_key=s.code_id.public_key
            e = self.env['hr.employee'].search( [('code_id.code','=',a.fingerprint_code)] )
            if e:
                a.employee_id = e.id
            else:
                a.employee_id=False

    @api.depends('task_code','site_code')
    def _get_site_and_task(self):
        for a in self:
            if a.verified:
                if a.site_code:
                    s = self.env['project.project'].search( [('code_id.code','=',a.site_code)] )
                    print [s]
                    if s:
                        a.site_id=s.id
                if a.task_code:
                    t = self.env['project.task'].search( [('code_id.code','=',a.task_code)] )
                    print [t]
                    if t:
                        a.task_id=t.id
                if a.site_id and a.task_id and a.signed_msg:
                    a.msg_sha1=hashlib.sha1(a.signed_msg).hexdigest()
                    
    site_id=fields.Many2one('project.project',string='Site',compute='_get_site_and_task')
    task_id=fields.Many2one('project.task',string='Task',compute='_get_site_and_task')
    msg_sha1=fields.Char('TimeSheet SHA1', compute='_get_site_and_task')
    #site_id=fields.Many2one('project.project',string='Site')
    #task_id=fields.Many2one('project.task',string='Task')

    def award_hours(self):
        for a in self:
            if a.verified and a.msg_sha1 and a.employee_id and a.site_id and a.task_id:
                t_exist=self.env['account.analytic.line'].search( [('name','=',a.msg_sha1)] )
                val={'user_id':a.employee_id.user_id.id,
                     'name':a.msg_sha1,
                     'project_id':a.site_id.id,
                     'task_id':a.task_id.id,
                     'unit_amount':a.worked_hours,
                     'date':a.check_out}
                #print t_exist, val
                if t_exist:
                    t_exist.write(val)
                else:
                    t_ = self.env['account.analytic.line'].create(val)
                    

    @api.depends('signed_msg', 'signature','site_public_key',)
    def _verified(self):
        for a in self:
            if a.signed_msg and a.signature and a.site_public_key:
                a.verified=ecdsa_verify(str(a.signed_msg), 
                                        str(a.signature), 
                                        str(a.site_public_key)
                )

            else:
                a.verified=False

    @api.multi
    def name_getAA(self):
        result = []
        for attendance in self:
            if not attendance.check_out:
                result.append((attendance.id, _("%(empl_name)s from %(check_in)s") % {
                    'empl_name': attendance.employee_id.name_related,
                    'check_in': fields.Datetime.to_string(fields.Datetime.context_timestamp(attendance, fields.Datetime.from_string(attendance.check_in))),
                }))
            else:
                result.append((attendance.id, _("%(empl_name)s from %(check_in)s to %(check_out)s") % {
                    'empl_name': attendance.employee_id.name_related,
                    'check_in': fields.Datetime.to_string(fields.Datetime.context_timestamp(attendance, fields.Datetime.from_string(attendance.check_in))),
                    'check_out': fields.Datetime.to_string(fields.Datetime.context_timestamp(attendance, fields.Datetime.from_string(attendance.check_out))),
                }))
        return result

    @api.depends('check_in', 'check_out')
    def _compute_worked_hours(self):
        for attendance in self:
            if attendance.check_out:
                delta = datetime.strptime(attendance.check_out, DEFAULT_SERVER_DATETIME_FORMAT) - datetime.strptime(attendance.check_in, DEFAULT_SERVER_DATETIME_FORMAT)
                a=attendance
                #print 44*'_'
                #print [a.check_out, a.check_in, delta]
                attendance.worked_hours = delta.total_seconds() / 3600.0

    @api.constrains('check_in', 'check_out')
    def _check_validity_check_in_check_out(self):
        """ verifies if check_in is earlier than check_out. """
        for attendance in self:
            if attendance.check_in and attendance.check_out:
                if attendance.check_out < attendance.check_in:
                    raise exceptions.ValidationError(_('"Check Out" time cannot be earlier than "Check In" time.'))

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        """ Verifies the validity of the attendance record compared to the others from the same employee.
            For the same employee we must have :
                * maximum 1 "open" attendance record (without check_out)
                * no overlapping time slices with previous employee records
        """
        for attendance in self:
            # we take the latest attendance before our check_in time and check it doesn't overlap with ours
            last_attendance_before_check_in = self.env['hr.attendance'].search([
                ('employee_id', '=', attendance.employee_id.id),
                ('check_in', '<=', attendance.check_in),
                ('id', '!=', attendance.id),
            ], order='check_in desc', limit=1)
            if last_attendance_before_check_in and last_attendance_before_check_in.check_out and last_attendance_before_check_in.check_out >= attendance.check_in:
                raise exceptions.ValidationError(_("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
                    'empl_name': attendance.employee_id.name_related,
                    'datetime': fields.Datetime.to_string(fields.Datetime.context_timestamp(self, fields.Datetime.from_string(attendance.check_in))),
                })

            if not attendance.check_out:
                # if our attendance is "open" (no check_out), we verify there is no other "open" attendance
                no_check_out_attendances = self.env['hr.attendance'].search([
                    ('employee_id', '=', attendance.employee_id.id),
                    ('check_out', '=', False),
                    ('id', '!=', attendance.id),
                ])
                if no_check_out_attendances:
                    raise exceptions.ValidationError(_("Cannot create new attendance record for %(empl_name)s, the employee hasn't checked out since %(datetime)s") % {
                        'empl_name': attendance.employee_id.name_related,
                        'datetime': fields.Datetime.to_string(fields.Datetime.context_timestamp(self, fields.Datetime.from_string(no_check_out_attendances.check_in))),
                    })
            else:
                # we verify that the latest attendance with check_in time before our check_out time
                # is the same as the one before our check_in time computed before, otherwise it overlaps
                last_attendance_before_check_out = self.env['hr.attendance'].search([
                    ('employee_id', '=', attendance.employee_id.id),
                    ('check_in', '<', attendance.check_out),
                    ('id', '!=', attendance.id),
                ], order='check_in desc', limit=1)
                if last_attendance_before_check_out and last_attendance_before_check_in != last_attendance_before_check_out:
                    raise exceptions.ValidationError(_("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
                        'empl_name': attendance.employee_id.name_related,
                        'datetime': fields.Datetime.to_string(fields.Datetime.context_timestamp(self, fields.Datetime.from_string(last_attendance_before_check_out.check_in))),
                    })

    @api.multi
    def copy(self):
        raise exceptions.UserError(_('You cannot duplicate an attendance.'))
