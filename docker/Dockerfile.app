###################################
###### Build from base image ######
###################################
FROM flail/flail:base

#################################################
####### Add extra packages if not on base #######
#################################################

###################################
####### Install source code #######
###################################

# Copy over nginx config
COPY ./flail/config/nginx/flail_nginx.conf /etc/nginx/sites-available/flail_nginx.conf
RUN ln -s /src/flail/config/nginx/flail_nginx.conf /etc/nginx/sites-enabled/

# Remove existing source code from base image
RUN mkdir -p /src
ADD . / /src/
WORKDIR /src
RUN pip install ../src

ENTRYPOINT ["/usr/bin/env"]
