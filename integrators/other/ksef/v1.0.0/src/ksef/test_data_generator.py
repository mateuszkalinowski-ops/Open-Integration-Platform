"""Generate KSeF test environment credentials (NIP + token) using self-signed certificates.

This module automates the full flow on the KSeF TE (api-test.ksef.mf.gov.pl):
1. Generate a valid NIP and self-signed certificate with TINPL-{NIP}
2. Create a test person via /testdata/person
3. Authenticate with XAdES-BES enveloped signature
4. Generate a KSeF token via POST /tokens
"""

import base64
import hashlib
import logging
import random
import re
from datetime import datetime, timezone
from typing import Any

import httpx
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from lxml import etree

logger = logging.getLogger(__name__)

TE_API_URL = "https://api-test.ksef.mf.gov.pl/api/v2"

AUTH_NS = "http://ksef.mf.gov.pl/auth/token/2.0"
DS_NS = "http://www.w3.org/2000/09/xmldsig#"
XADES_NS = "http://uri.etsi.org/01903/v1.3.2#"
C14N_ALG = "http://www.w3.org/TR/2001/REC-xml-c14n-20010315"
SIG_ALG = "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"
DIGEST_ALG = "http://www.w3.org/2001/04/xmlenc#sha256"
ENVELOPE_TRANSFORM = "http://www.w3.org/2000/09/xmldsig#enveloped-signature"


def _generate_valid_nip() -> str:
    weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]
    while True:
        digits = [random.randint(1, 9)]
        for _ in range(8):
            digits.append(random.randint(0, 9))
        checksum = sum(d * w for d, w in zip(digits, weights)) % 11
        if checksum < 10:
            digits.append(checksum)
            nip = "".join(str(d) for d in digits)
            if re.match(r"^[1-9]((\d[1-9])|([1-9]\d))\d{7}$", nip):
                return nip


def _generate_valid_pesel() -> str:
    pesel_base = (
        f"{random.randint(80, 99):02d}"
        f"{random.randint(1, 12):02d}"
        f"{random.randint(1, 28):02d}"
        f"{random.randint(0, 9999):04d}"
    )
    pw = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]
    ck = (10 - sum(int(d) * w for d, w in zip(pesel_base, pw)) % 10) % 10
    return pesel_base + str(ck)


def _generate_self_signed_cert(nip: str) -> tuple[rsa.RSAPrivateKey, x509.Certificate]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "PL"),
        x509.NameAttribute(NameOID.COMMON_NAME, "OIP Test Person"),
        x509.NameAttribute(NameOID.GIVEN_NAME, "Test"),
        x509.NameAttribute(NameOID.SURNAME, "User"),
        x509.NameAttribute(NameOID.SERIAL_NUMBER, f"TINPL-{nip}"),
    ])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime(2025, 1, 1, tzinfo=timezone.utc))
        .not_valid_after(datetime(2027, 12, 31, tzinfo=timezone.utc))
        .sign(key, hashes.SHA256())
    )
    return key, cert


def _c14n(element: etree._Element) -> bytes:
    return etree.tostring(element, method="c14n", exclusive=False, with_comments=False)


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _build_xades_bes_signed_xml(
    xml_bytes: bytes,
    private_key: rsa.RSAPrivateKey,
    cert: x509.Certificate,
) -> bytes:
    root = etree.fromstring(xml_bytes)
    ds = DS_NS
    xades = XADES_NS

    cert_der = cert.public_bytes(serialization.Encoding.DER)
    cert_b64 = _b64(cert_der)
    cert_digest_b64 = _b64(_sha256(cert_der))
    issuer_name = cert.issuer.rfc4514_string()
    serial_number = str(cert.serial_number)
    signing_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    sig_id = "Signature-1"
    sp_id = "SignedProperties-1"

    signature_el = etree.SubElement(root, f"{{{ds}}}Signature", nsmap={"ds": ds})
    signature_el.set("Id", sig_id)

    signed_info = etree.SubElement(signature_el, f"{{{ds}}}SignedInfo")
    etree.SubElement(signed_info, f"{{{ds}}}CanonicalizationMethod").set("Algorithm", C14N_ALG)
    etree.SubElement(signed_info, f"{{{ds}}}SignatureMethod").set("Algorithm", SIG_ALG)

    ref1 = etree.SubElement(signed_info, f"{{{ds}}}Reference")
    ref1.set("URI", "")
    transforms = etree.SubElement(ref1, f"{{{ds}}}Transforms")
    etree.SubElement(transforms, f"{{{ds}}}Transform").set("Algorithm", ENVELOPE_TRANSFORM)
    etree.SubElement(transforms, f"{{{ds}}}Transform").set("Algorithm", C14N_ALG)
    etree.SubElement(ref1, f"{{{ds}}}DigestMethod").set("Algorithm", DIGEST_ALG)
    dv1 = etree.SubElement(ref1, f"{{{ds}}}DigestValue")

    ref2 = etree.SubElement(signed_info, f"{{{ds}}}Reference")
    ref2.set("URI", f"#{sp_id}")
    ref2.set("Type", "http://uri.etsi.org/01903#SignedProperties")
    etree.SubElement(ref2, f"{{{ds}}}DigestMethod").set("Algorithm", DIGEST_ALG)
    dv2 = etree.SubElement(ref2, f"{{{ds}}}DigestValue")

    sig_value_el = etree.SubElement(signature_el, f"{{{ds}}}SignatureValue")

    key_info = etree.SubElement(signature_el, f"{{{ds}}}KeyInfo")
    x509_data = etree.SubElement(key_info, f"{{{ds}}}X509Data")
    x509_cert_el = etree.SubElement(x509_data, f"{{{ds}}}X509Certificate")
    x509_cert_el.text = cert_b64

    obj = etree.SubElement(signature_el, f"{{{ds}}}Object")
    qp = etree.SubElement(obj, f"{{{xades}}}QualifyingProperties", nsmap={"xades": xades})
    qp.set("Target", f"#{sig_id}")
    sp = etree.SubElement(qp, f"{{{xades}}}SignedProperties")
    sp.set("Id", sp_id)
    ssp = etree.SubElement(sp, f"{{{xades}}}SignedSignatureProperties")
    st_el = etree.SubElement(ssp, f"{{{xades}}}SigningTime")
    st_el.text = signing_time
    sc = etree.SubElement(ssp, f"{{{xades}}}SigningCertificate")
    sc_cert = etree.SubElement(sc, f"{{{xades}}}Cert")
    cd = etree.SubElement(sc_cert, f"{{{xades}}}CertDigest")
    etree.SubElement(cd, f"{{{ds}}}DigestMethod").set("Algorithm", DIGEST_ALG)
    etree.SubElement(cd, f"{{{ds}}}DigestValue").text = cert_digest_b64
    issuer_serial = etree.SubElement(sc_cert, f"{{{xades}}}IssuerSerial")
    etree.SubElement(issuer_serial, f"{{{ds}}}X509IssuerName").text = issuer_name
    etree.SubElement(issuer_serial, f"{{{ds}}}X509SerialNumber").text = serial_number

    signature_el.getparent().remove(signature_el)
    dv1.text = _b64(_sha256(_c14n(root)))
    root.append(signature_el)

    dv2.text = _b64(_sha256(_c14n(sp)))

    si_c14n = _c14n(signed_info)
    sig_value_el.text = _b64(private_key.sign(si_c14n, asym_padding.PKCS1v15(), hashes.SHA256()))

    return etree.tostring(root, xml_declaration=True, encoding="UTF-8")


async def generate_test_credentials() -> dict[str, Any]:
    """Generate a fresh NIP + KSeF token on the test environment.

    Returns dict with keys: nip, ksef_token, environment, reference_number.
    Raises RuntimeError on failure.
    """
    nip = _generate_valid_nip()
    pesel = _generate_valid_pesel()
    private_key, cert = _generate_self_signed_cert(nip)

    logger.info("Generating test credentials for NIP=%s***", nip[:6])

    # verify=False is intentional: KSeF TE uses self-signed/test certificates
    async with httpx.AsyncClient(timeout=30.0, verify=False) as client:  # noqa: S501
        # 1. Create test person
        resp = await client.post(
            f"{TE_API_URL}/testdata/person",
            json={"nip": nip, "pesel": pesel, "isBailiff": False, "description": "OIP auto-generated test person"},
        )
        if resp.status_code not in (200, 400):
            raise RuntimeError(f"Failed to create test person: {resp.status_code} {resp.text[:200]}")

        # 2. Get challenge
        resp = await client.post(f"{TE_API_URL}/auth/challenge")
        resp.raise_for_status()
        challenge = resp.json()["challenge"]

        # 3. Build and sign AuthTokenRequest XML (XAdES-BES)
        nsmap = {None: AUTH_NS}
        root = etree.Element(f"{{{AUTH_NS}}}AuthTokenRequest", nsmap=nsmap)
        etree.SubElement(root, f"{{{AUTH_NS}}}Challenge").text = challenge
        ctx = etree.SubElement(root, f"{{{AUTH_NS}}}ContextIdentifier")
        etree.SubElement(ctx, f"{{{AUTH_NS}}}Nip").text = nip
        etree.SubElement(root, f"{{{AUTH_NS}}}SubjectIdentifierType").text = "certificateSubject"

        unsigned_xml = etree.tostring(root, xml_declaration=True, encoding="UTF-8")
        signed_xml = _build_xades_bes_signed_xml(unsigned_xml, private_key, cert)

        # 4. Submit XAdES signature
        resp = await client.post(
            f"{TE_API_URL}/auth/xades-signature",
            content=signed_xml,
            headers={"Content-Type": "application/xml"},
            params={"verifyCertificateChain": "false"},
        )
        if resp.status_code not in (200, 202):
            raise RuntimeError(f"XAdES auth failed: {resp.status_code} {resp.text[:300]}")

        auth_data = resp.json()
        auth_token = auth_data["authenticationToken"]["token"]
        ref = auth_data["referenceNumber"]

        # 5. Poll auth status
        import asyncio

        for _ in range(15):
            await asyncio.sleep(2)
            resp = await client.get(
                f"{TE_API_URL}/auth/{ref}",
                headers={"Authorization": f"Bearer {auth_token}"},
            )
            if resp.status_code == 200:
                status_code = resp.json().get("status", {}).get("code")
                if status_code == 200:
                    break
                if status_code and status_code >= 400:
                    details = resp.json().get("status", {}).get("details", [])
                    raise RuntimeError(f"Auth failed with status {status_code}: {details}")
        else:
            raise RuntimeError("Authentication timed out")

        # 6. Redeem access token
        resp = await client.post(
            f"{TE_API_URL}/auth/token/redeem",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        resp.raise_for_status()
        access_token = resp.json()["accessToken"]["token"]

        # 7. Generate KSeF token
        resp = await client.post(
            f"{TE_API_URL}/tokens",
            json={
                "permissions": ["InvoiceRead", "InvoiceWrite", "CredentialsRead", "Introspection"],
                "description": "OIP auto-generated test token",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if resp.status_code not in (200, 202):
            raise RuntimeError(f"Token generation failed: {resp.status_code} {resp.text[:300]}")

        token_data = resp.json()
        ksef_token = token_data["token"]
        token_ref = token_data["referenceNumber"]

        logger.info("Test credentials generated: NIP=%s, ref=%s", nip, token_ref)

        return {
            "nip": nip,
            "ksef_token": ksef_token,
            "environment": "test",
            "reference_number": token_ref,
        }
