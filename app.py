from config import app, db
from routes import main
from flask import Flask, make_response

app.register_blueprint(main)

if __name__ == '__main__':
    db.create_all()  # Create tables if not already present
    app.run(debug=True)

@app.after_request
def set_security_headers(response):
    # Content Security Policy
    # WARNING: the following is a very restrictive policy just as an example.
    # You'll need to customize the `default-src` directive to allow for your site's requirements.
    # For example, if you load resources from CDN like scripts, styles, or images, you must include those domains in 'default-src'.
    # Example CSP allowing resources to be loaded from self domain as well as some external domains
    response.headers['Content-Security-Policy'] = (
        "default-src 'self';"
        "script-src 'self' https://code.jquery.com https://cdnjs.cloudflare.com https://maxcdn.bootstrapcdn.com;"
        "style-src 'self' https://fonts.googleapis.com https://maxcdn.bootstrapcdn.com;"
        "img-src 'self' data:;"
        "font-src 'self' https://fonts.gstatic.com;"
        "object-src 'none';"
    )

    # HTTP Strict Transport Security
    # max-age is the time in seconds that the browser should remember that a site is only to be accessed using HTTPS.
    # includeSubDomains ensures that the rule also applies to all subdomains.
    response.headers['Strict-Transport-Security'] = 'max-age=63072000; includeSubDomains'

    # X-Content-Type-Options
    response.headers['X-Content-Type-Options'] = 'nosniff'

    # X-Frame-Options
    response.headers['X-Frame-Options'] = 'DENY'  # DENY ensures that your site cannot be put into an iframe.

    # X-XSS-Protection
    # "1; mode=block" enables XSS filtering. Rather than sanitizing the page, the browser will prevent rendering of the page if an attack is detected.
    response.headers['X-XSS-Protection'] = '1; mode=block'

    return response