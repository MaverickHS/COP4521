# Maverick's Flask Server -- COP4521 Fall Project

## Description

This project is a Python web application developed for COP4521, focusing on Python web application development. The goal is to create a Flask-based web application that displays news from the Hacker News portal. The application features pages for Sign Up/Login, News Feed, Profile, and Admin. Users can interact with news items using Like and Dislike buttons, and the most popular items are displayed at the top of the news feed. The Auth0 platform is used for user identity validation, and an SQLite database is employed to store data securely.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Configs](#configs)
- [Testing](#testing)

## Features

- Users can sign up and log in securely with Google email through Auth0.
- The News Feed displays the latest news items from the Hacker News portal, paginated and sorted by time and popularity.
- Admin functionalities include deleting news items and related likes/dislikes or deleting a user and their associated data.
- Scheduled updates from the Hacker News API are implemented through a cron job.
- Security measures include HTTPS enforcement, SSH accessibility with public key authentication, and firewall configurations.

## Installation

- Set up the server with Nginx and Gunicorn.
- Install necessary libraries using the provided requirements.txt.
- Configure necessary files for Nginx, supervisor, Gunicorn, and Cron.
- Follow steps to ensure secure SSH accessibility and HTTPS enforcement.
- Test the installation using commands.

## Configs
- Flask for web hosting
- SQLite3 for database hosting
- SQLAlchemy for retrieving data from tables
- 0Auth for Google login and managing users

## Testing
Certainly! Let's expand the testing section to provide more comprehensive details:

### Unit Testing

- Ensure all unit tests are included in the repository.
- Achieve a unit test coverage of more than 80% to meet project requirements.
- Run unit tests using the following command:

  ```bash
  python -m unittest discover -s tests
  ```

### Security Testing

#### HTTPS and SSH Accessibility

- Confirm HTTPS enforcement for web services by modifying the Nginx site configuration file to listen on port 443 with appropriate SSL/TLS settings.
- Restrict HTTP access and configure a redirect from HTTP to HTTPS.
- Test SSH accessibility without a password using the following command:

  ```bash
  ssh -i ~/.ssh/id_rsa grader@<server_ip_address> -p 2048
  ```

#### No Password Authentication

- Ensure SSH is accessible only through public key authentication by setting `PasswordAuthentication` to `no` in the `sshd_config` file.

#### Mozilla Observatory Report

- Generate a Mozilla Observatory report by visiting [Mozilla Observatory](https://observatory.mozilla.org/) and inputting your server's domain name or IP address.
- Follow instructions on the website to obtain the report, and include the final score in your project report.

### Firewall Testing and Miscellaneous

#### Open Ports

- List open ports and check UFW status using the following command:

  ```bash
  sudo ufw status
  ```

#### White Listed IPs

- Configure UFW to allow access only from whitelisted IP addresses using the `ufw allow` command to specify open ports and allowed IP addresses.

#### Configuration Testing

- Check the SSH configuration by examining the SSH server configuration file:

  ```bash
  vi /etc/ssh/sshd_config
  ```

- Verify the Nginx configuration by examining the site-specific configuration file located in `/etc/nginx/sites-enabled/`.
  
- Ensure Gunicorn service is running and Flask application is served using Gunicorn by examining the systemd service file for your project located in `/etc/systemd/system/`.

#### Nginx and Project Service Status

- Check the status of Nginx using:

  ```bash
  sudo nginx -t
  ```

- Check the status of your project-specific service using:

  ```bash
  sudo systemctl status <project>
  ```

### Lynis Hardening Index

- Run Lynis to assess the server's hardening index:

  ```bash
  lynis audit system
  ```

- Aim for a high Lynis score to ensure the system's security.

These comprehensive tests cover unit testing, security testing, and miscellaneous configurations, ensuring a robust and secure web application deployment.