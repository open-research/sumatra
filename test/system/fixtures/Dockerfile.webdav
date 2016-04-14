#
# For testing Sumatra's webdav remote store support
#
#
# Usage:  docker build -t webdav_test -f Dockerfile.webdav .

FROM debian:jessie
MAINTAINER andrew.davison@unic.cnrs-gif.fr

RUN apt-get update
RUN apt-get -y -q install apache2
RUN a2enmod dav
RUN a2enmod dav_fs

RUN mkdir /var/www/webdav
RUN chown www-data:www-data /var/www/webdav
COPY apache_webdav.conf /etc/apache2/sites-available/
RUN htpasswd -c -b /var/www/webdav.password sumatra sumatra
RUN a2ensite apache_webdav.conf

EXPOSE 80

CMD ["/usr/sbin/apache2ctl", "-D",  "FOREGROUND"]