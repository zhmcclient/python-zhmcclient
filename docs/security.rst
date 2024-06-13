.. Copyright 2021 IBM Corp. All Rights Reserved.
..
.. Licensed under the Apache License, Version 2.0 (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..    http://www.apache.org/licenses/LICENSE-2.0
..
.. Unless required by applicable law or agreed to in writing, software
.. distributed under the License is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.
..

.. _`Security`:

Security
========

This section contains information about the security of the communication
between the 'zhmcclient' client and the HMC.


.. _`HMC Web Services API`:

HMC Web Services API
--------------------

This section covers the communication between the 'zhmcclient' package
and the HMC Web Services API on port 6794. The 'zhmcclient' package uses the
`Python 'requests' package <https://pypi.org/project/requests/>`_
for this purpose.

SSL/TLS protocol version
^^^^^^^^^^^^^^^^^^^^^^^^

The HMC supports HTTPS at its Web Services API port, i.e. it requires the use
of SSL/TLS-based sockets. The HMC can be configured to require TLS 1.2, or to
tolerate the older SSLv3 protocol in addition. Since SSLv3 is considered
insecure, it is highly recommended to configure the HMC to require TLS 1.2 and
to disable SSLv3 and RC4. This can be configured in the HMC task
"Customize Console Services". See also the :term:`HMC Security` book and
Chapter 3 "Invoking API operations" in the :term:`HMC API` book.

The 'zhmcclient' package uses the default settings of the 'requests' package
regarding the SSL/TLS version, which causes the highest version supported by
both client and HMC to be used. The highest supported SSL/TLS version used by
the client is determined by the OpenSSL version used by Python on the client
side. OpenSSL 1.0.1 or higher is required to support TLS 1.2.
You can display the OpenSSL version used by Python using this command:

.. code-block:: bash

    $ python -c "import ssl; print(ssl.OPENSSL_VERSION)"
    OpenSSL 1.1.1i  8 Dec 2020


.. _`HMC certificate`:

HMC certificate
^^^^^^^^^^^^^^^

By default, the HMC is configured with a self-signed certificate. That is the
X.509 certificate presented by the HMC as the server certificate during SSL/TLS
handshake at its Web Services API.

Starting with version 0.31, the zhmcclient will reject self-signed certificates
by default.

The HMC should be configured to use a CA-verifiable certificate. This can be
done in the HMC task "Certificate Management". See also the :term:`HMC Security`
book and Chapter 3 "Invoking API operations" in the :term:`HMC API` book.

Starting with version 0.31, the zhmcclient provides a control knob for the
verification of the HMC certificate via the ``verify_cert`` init parameter of
the :class:`zhmcclient.Session` class. That init parameter can be set to:

* `False`: Do not verify the HMC certificate. Not verifying the HMC certificate
  means the zhmcclient will not detect hostname mismatches, expired
  certificates, revoked certificates, or otherwise invalid certificates. Since
  this mode makes the connection vulnerable to man-in-the-middle attacks, it
  is insecure and should not be used in production environments.

* `True` (default): Verify the HMC certificate using the CA certificates from
  the first of these locations:

  - The file or directory in the ``REQUESTS_CA_BUNDLE`` env.var, if set
  - The file or directory in the ``CURL_CA_BUNDLE`` env.var, if set
  - The `Python 'certifi' package <https://pypi.org/project/certifi/>`_
    (which contains the
    `Mozilla Included CA Certificate List <https://wiki.mozilla.org/CA/Included_Certificates>`_).

* :term:`string`: Path name of a certificate file or directory. Verify the HMC
  certificate using the CA certificates in that file or directory.

If a certificate file is specified (using any of the ways listed above), that
file must be in PEM format and must contain all CA certificates that are
supposed to be used.  Usually they are in the order from leaf to root, but
that is not a hard requirement. The single certificates are concatenated
in the file.

If a certificate directory is specified (using any of the ways listed above),
it must contain PEM files with all CA certificates that are supposed to be used,
and copies of the PEM files or symbolic links to them in the hashed format
created by the OpenSSL command ``c_rehash``.

An X.509 certificate in PEM format is base64-encoded, begins with the line
``-----BEGIN CERTIFICATE-----``, and ends with the line
``-----END CERTIFICATE-----``.
More information about the PEM format is for example on this
`www.ssl.com page <https://www.ssl.com/guide/pem-der-crt-and-cer-x-509-encodings-and-conversions>`_
or in this `serverfault.com answer <https://serverfault.com/a/9717/330351>`_.

Since the zhmcclient package uses the 'requests' package for the communication
with the Web Services API of the HMC, the behavior described above actually
comes from the 'requests' package. Unfortunately, its documentation about
certificate verification is somewhat brief, see
`SSL Cert Verification <https://docs.python-requests.org/en/master/user/advanced/#ssl-cert-verification>`_.

Note that setting the ``REQUESTS_CA_BUNDLE`` or ``CURL_CA_BUNDLE`` environment
variables influences other programs that use these variables, too.


.. _`Cipher suites`:

Cipher suites
^^^^^^^^^^^^^

During SSL/TLS handshake, the cipher suite to be used for various aspects in the
communication is negotiated between the HMC and the 'zhmcclient' client.

The set of cipher suites enabled for the HMC Web Services API can be configured
in the HMC task "Certificate Management".
See also the :term:`HMC Security` book for details.

The 'zhmcclient' package uses the default cipher suites of the 'requests'
package, which are the default cipher suites used by the standard Python 'ssl'
module. By default, the CPython implementation uses OpenSSL.
`Python PEP 644 <https://www.python.org/dev/peps/pep-0644/>`_ targeted for
Python 3.10 contains information about which versions of Python support which
versions of OpenSSL.

As of Python 3.9, there is no function yet that lists the supported ciphers.

You can display the OpenSSL version used by the Python on your system with
this command:

.. code-block:: bash

    $ python -c "import ssl; print(ssl.OPENSSL_VERSION)"
    OpenSSL 1.1.1i  8 Dec 2020

The TLS 1.2 compatible ciphers that are supported by OpenSSL on your system can
be listed with this command:

.. code-block:: bash

    $ openssl ciphers -tls1_2 -s -v | sort
    AES128-GCM-SHA256  TLSv1.2  Kx=RSA  Au=RSA  Enc=AESGCM(128)  Mac=AEAD
    AES128-SHA         SSLv3    Kx=RSA  Au=RSA  Enc=AES(128)     Mac=SHA1
    AES128-SHA256      TLSv1.2  Kx=RSA  Au=RSA  Enc=AES(128)     Mac=SHA256
    . . .

The SSL/TLS version shown in the output is the *minimum* SSL/TLS protocol
version needed to use the cipher, not the actual version that is used.

Brief expansion of the output field names used by this command:

* Kx = Key Exchange
* Au = Authentication
* Enc = Encryption
* Mac = Message Authentication Code


.. _`HMC Web Services API notifications`:

HMC Web Services API notifications
----------------------------------

The HMC Web Services API supports notifications that are sent from the HMC to
a client. The HMC supports two protocols for this purpose:

* STOMP (Streaming Text Oriented Messaging Protocol) on port 61612.
* OpenWire on port 61617.

These protocols can be enabled on the HMC task "Customize API Settings".
See also the :term:`HMC Security` book for details.

The 'zhmcclient' package supports the STOMP protocol for HMC notifications and
uses the
`Python 'stomp-py' package <https://pypi.org/project/stomp-py/>`_
for this purpose.
