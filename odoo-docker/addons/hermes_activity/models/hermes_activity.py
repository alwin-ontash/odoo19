from odoo import models, fields


class HermesActivity(models.Model):
    _name = 'hermes.activity'
    _description = 'Hermes Activity Log'
    _order = 'date desc, id desc'
    _rec_name = 'query'

    query = fields.Char(
        string='Query',
        required=True,
        help='The natural-language query sent by the user via Telegram/Hermes',
    )
    source = fields.Selection(
        selection=[
            ('telegram', 'Telegram'),
            ('api', 'API'),
            ('test', 'Test'),
        ],
        string='Source',
        required=True,
        default='telegram',
    )
    tool_called = fields.Char(
        string='MCP Tool Called',
        help='Name of the MCP tool that was invoked to handle this query',
    )
    response = fields.Text(
        string='Response',
        help='Summary of the response returned to the user',
    )
    date = fields.Datetime(
        string='Date',
        required=True,
        default=fields.Datetime.now,
    )
    state = fields.Selection(
        selection=[
            ('pending', 'Pending'),
            ('success', 'Success'),
            ('error', 'Error'),
        ],
        string='Status',
        required=True,
        default='success',
    )
    notes = fields.Text(string='Notes')
