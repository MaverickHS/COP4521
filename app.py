"""
This module sets up the Flask application and its routes, database, and security configurations.
"""

from routes import main
from config import app, db

app.register_blueprint(main)

@app.after_request
def set_security_headers(response):
    """
    Set security headers on each response to enhance security.
    """
    # Content Security Policy
    csp = (
        "default-src 'self'; "
        "script-src 'self' https://code.jquery.com https://cdnjs.cloudflare.com "
        "https://maxcdn.bootstrapcdn.com; "
        "style-src 'self' https://fonts.googleapis.com https://maxcdn.bootstrapcdn.com; "
        "img-src 'self' data:; "
        "font-src 'self' https://fonts.gstatic.com; "
        "object-src 'none';"
    )

    # HTTP Strict Transport Security
    hsts = 'max-age=63072000; includeSubDomains'

    # X-Content-Type-Options
    xtype_options = 'nosniff'

    # X-Frame-Options
    xframe_options = 'DENY'  # DENY ensures that your site cannot be put into an iframe.

    # X-XSS-Protection
    xxss_protection = '1; mode=block'  # Enables XSS filtering.

    # Set headers
    response.headers['Content-Security-Policy'] = csp
    response.headers['Strict-Transport-Security'] = hsts
    response.headers['X-Content-Type-Options'] = xtype_options
    response.headers['X-Frame-Options'] = xframe_options
    response.headers['X-XSS-Protection'] = xxss_protection

    return response


if __name__ == '__main__':
    db.create_all()  # Create tables if not already present
    app.run(debug=True)
