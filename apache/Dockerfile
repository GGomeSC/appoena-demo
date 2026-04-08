FROM httpd:2.4

COPY apache/conf/httpd.conf /usr/local/apache2/conf/httpd.conf
COPY apache/www/ /usr/local/apache2/htdocs/
COPY apache/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["httpd-foreground"]
