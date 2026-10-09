FROM postgres:18-bookworm
RUN localedef -i ru_RU -c -f UTF-8 -A /usr/share/locale/locale.alias ru_RU.UTF-8
ENV LANG=ru_RU.UTF-8
COPY postgres/postgresql.conf /etc/postgresql/postgresql.conf
COPY postgres/01-init.sql /docker-entrypoint-initdb.d/01-init.sql
CMD ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf"]
