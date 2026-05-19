{
    'name': 'Hermes Activity Log',
    'version': '19.0.1.0.0',
    'summary': 'Track Hermes MCP agent activity and queries in Odoo',
    'description': """
        Hermes Activity Log
        ===================
        Logs all queries and responses exchanged between the Hermes agent
        and Odoo via the MCP protocol. Useful for auditing and debugging
        the Telegram → Hermes → Odoo integration.
    """,
    'author': 'MuK IT',
    'category': 'Productivity',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/hermes_activity_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
