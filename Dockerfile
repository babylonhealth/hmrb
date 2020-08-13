FROM bodak/rust-python-alpine

# RUN apk add --no-cache cython libffi-dev sqlite-dev make
RUN pip3 install cython
RUN pip3 install --no-cache-dir --ignore-installed nox

COPY . .
