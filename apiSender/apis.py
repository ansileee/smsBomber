API_CONFIGS = [
    
    # API 1
{
    "name": "Addatimes",
    "method": "POST",
    "url": "https://app.addatimes.com/api/login",
    "headers": {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json",
        "origin": "https://www.addatimes.com",
        "referer": "https://www.addatimes.com/",
        "user-agent": "Mozilla/5.0"
    },
    "json": {
        "phone": "{phone}",
        "country_code": "IN"
    }
},

# API 2
{
    "name": "Addatimes",
    "method": "POST",
    "url": "https://app.addatimes.com/api/register",
    "headers": {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json",
        "origin": "https://www.addatimes.com",
        "referer": "https://www.addatimes.com/",
        "user-agent": "Mozilla/5.0"
    },
    "json": {
        "phone": "{phone}",
        "email": "{random_email}",
        "country_code": "IN",
        "password": "elliotisdop666",
        "confirm_password": "elliotisdop666"
    }
},

# API 3
{
    "name": "Allen",
    "method": "POST",
    "url": "https://api.allen-live.in/api/v1/auth/sendOtp",
    "headers": {
        "Content-Type": "application/json",
        "x-device-id": "{uuid}",
        "x-client-type": "web"
    },
    "params": {
        "center_id": "",
        "source": "home-page-login"
    },
    "json": {
        "country_code": "91",
        "phone_number": "{phone}",
        "persona_type": "STUDENT",
        "otp_type": "SHARED_DEFAULT"
    }
},

# API 4
{
    "name": "Chaupal",
    "method": "POST",
    "url": "https://chaupalapi.revlet.net/service/api/auth/get/otp",
    "headers": {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json",
        "box-id": "29c1f5fb-53d2-cc40-fe6b-3f4e2b21471e",
        "session-id": "d14cad2f-2cb9-4211-81bc-7eb63271bbfe",
        "tenant-code": "chaupal",
        "origin": "https://www.chaupal.com",
        "referer": "https://www.chaupal.com/",
        "user-agent": "Mozilla/5.0"
    },
    "json": {
        "context": "signup",
        "mobile": "91{phone}"
    }
},

# API 5
{
    "name": "CityMall",
    "method": "POST",
    "url": "https://citymall.live/web-api/auth/send-otp",
    "headers": {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://citymall.live",
        "Referer": "https://citymall.live/",
        "User-Agent": "Mozilla/5.0"
    },
    "cookies": {
        "cm_guest": "{uuid}"
    },
    "json": {
        "phone_number": "{phone}"
    }
},

# API 6
{
    "name": "Delhivery",
    "method": "GET",
    "url": "https://dlv-api.delhivery.com/v4/otp/generate/{phone}",
    "headers": {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "origin": "https://www.delhivery.com",
        "referer": "https://www.delhivery.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "x-aws-waf-token": "f7c9b3d5-5738-4b52-9cf3-d82ba252c043:BQoAreKFvjxDAAAA:bOG69Fnp16TiGu9moYudpj1Yi5xCaWr3xypviyZWHxdOtyaSYF3pAUgow7Atx3L3rBPdN+Fv3QkhcRM6LB+asW1Fa1zxpBRvmwfaSTZ19TKp85ZjXiY5u0mIfvS32fRfPKnKLRixVrXoNvOQf+CICAOEPQbOAD11XGSFiNX7arUuLSV2dWWLJ+ySGHN1t09bcjuUNg=="
    }
},

# API 7
{
    "name": "Delhivery Login",
    "method": "GET",
    "url": "https://dlv-api.delhivery.com/v4/otp/generate/{phone}",
    "headers": {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "origin": "https://www.delhivery.com",
        "referer": "https://www.delhivery.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "x-aws-waf-token": "f7c9b3d5-5738-4b52-9cf3-d82ba252c043:BQoAreKFvjxDAAAA:bOG69Fnp16TiGu9moYudpj1Yi5xCaWr3xypviyZWHxdOtyaSYF3pAUgow7Atx3L3rBPdN+Fv3QkhcRM6LB+asW1Fa1zxpBRvmwfaSTZ19TKp85ZjXiY5u0mIfvS32fRfPKnKLRixVrXoNvOQf+CICAOEPQbOAD11XGSFiNX7arUuLSV2dWWLJ+ySGHN1t09bcjuUNg=="
    }
},

# API 8
{
    "name": "District",
    "method": "POST",
    "url": "https://www.district.in/gw/auth/generate_otp",
    "headers": {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.8",
        "content-type": "application/json",
        "origin": "https://www.district.in",
        "referer": "https://www.district.in/",
        "sec-ch-ua": "\"Not:A-Brand\";v=\"99\", \"Chromium\";v=\"145\", \"Brave\";v=\"145\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "x-app-type": "ed_web",
        "x-app-version": "11.11.1",
        "x-client-id": "district-web",
        "x-device-id": "{uuid}",
        "x-guest-token": "1212"
    },
    "cookies": {
        "x-device-id": "{uuid}"
    },
    "json": {
        "phone_number": "{phone}",
        "country_code": "91"
    }
},

# API 9
{
    "name": "Fi",
    "method": "POST",
    "url": "https://fi.money/next-api/grpc/Signup/generateOtp",
    "headers": {
        "accept": "*/*",
        "content-type": "application/json",
        "origin": "https://fi.money",
        "referer": "https://fi.money/features/instant-loans/personal-loan-eligibility",
        "user-agent": "Mozilla/5.0"
    },
    "cookies": {
        "prospect_id": "{uuid}",
        "server_prospect_id": "false"
    },
    "json": {
        "phoneNumber": {
            "countryCode": 91,
            "nationalNumber": "{phone}"
        },
        "token": "",
        "flowName": 0
    }
},

# API 10
{
    "name": "HDFCSky",
    "method": "POST",
    "url": "https://api.hdfcsky.com/api/kyc/v2/send-otp/sms",
    "headers": {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "origin": "https://hdfcsky.com",
        "referer": "https://hdfcsky.com/",
        "sec-ch-ua": "\"Not:A-Brand\";v=\"99\", \"Chromium\";v=\"120\", \"Google Chrome\";v=\"120\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "x-device-type": "web"
    },
    "json": {
        "phone_no": "91{phone}"
    }
},

# API 11
{
    "name": "Hoichoi",
    "method": "POST",
    "url": "https://prod-api.hoichoi.dev/core/api/v1/auth/signinup/code",
    "headers": {
        "content-type": "application/json",
        "rid": "anti-csrf",
        "st-auth-mode": "header"
    },
    "json": {
        "phoneNumber": "+91{phone}",
        "platform": "MOBILE_WEB"
    }
},

# API 6
{
    "name": "Delhivery",
    "method": "GET",
    "url": "https://dlv-api.delhivery.com/v4/otp/generate/{phone}",
    "headers": {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "origin": "https://www.delhivery.com",
        "referer": "https://www.delhivery.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "x-aws-waf-token": "f7c9b3d5-5738-4b52-9cf3-d82ba252c043:BQoAreKFvjxDAAAA:bOG69Fnp16TiGu9moYudpj1Yi5xCaWr3xypviyZWHxdOtyaSYF3pAUgow7Atx3L3rBPdN+Fv3QkhcRM6LB+asW1Fa1zxpBRvmwfaSTZ19TKp85ZjXiY5u0mIfvS32fRfPKnKLRixVrXoNvOQf+CICAOEPQbOAD11XGSFiNX7arUuLSV2dWWLJ+ySGHN1t09bcjuUNg=="
    }
},

# API 7
{
    "name": "Delhivery",
    "method": "GET",
    "url": "https://dlv-api.delhivery.com/v4/otp/generate/{phone}",
    "headers": {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "origin": "https://www.delhivery.com",
        "referer": "https://www.delhivery.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "x-aws-waf-token": "f7c9b3d5-5738-4b52-9cf3-d82ba252c043:BQoAreKFvjxDAAAA:bOG69Fnp16TiGu9moYudpj1Yi5xCaWr3xypviyZWHxdOtyaSYF3pAUgow7Atx3L3rBPdN+Fv3QkhcRM6LB+asW1Fa1zxpBRvmwfaSTZ19TKp85ZjXiY5u0mIfvS32fRfPKnKLRixVrXoNvOQf+CICAOEPQbOAD11XGSFiNX7arUuLSV2dWWLJ+ySGHN1t09bcjuUNg=="
    }
},

# API 8
{
    "name": "District",
    "method": "POST",
    "url": "https://www.district.in/gw/auth/generate_otp",
    "headers": {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.8",
        "content-type": "application/json",
        "origin": "https://www.district.in",
        "referer": "https://www.district.in/",
        "sec-ch-ua": "\"Not:A-Brand\";v=\"99\", \"Chromium\";v=\"145\", \"Brave\";v=\"145\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "x-app-type": "ed_web",
        "x-app-version": "11.11.1",
        "x-client-id": "district-web",
        "x-device-id": "{uuid}",
        "x-guest-token": "1212"
    },
    "cookies": {
        "x-device-id": "{uuid}"
    },
    "json": {
        "phone_number": "{phone}",
        "country_code": "91"
    }
},

# API 9
{
    "name": "Fi",
    "method": "POST",
    "url": "https://fi.money/next-api/grpc/Signup/generateOtp",
    "headers": {
        "accept": "*/*",
        "content-type": "application/json",
        "origin": "https://fi.money",
        "referer": "https://fi.money/features/instant-loans/personal-loan-eligibility",
        "user-agent": "Mozilla/5.0"
    },
    "cookies": {
        "prospect_id": "{uuid}",
        "server_prospect_id": "false"
    },
    "json": {
        "phoneNumber": {
            "countryCode": 91,
            "nationalNumber": "{phone}"
        },
        "token": "",
        "flowName": 0
    }
},

# API 10
{
    "name": "HDFCSky",
    "method": "POST",
    "url": "https://api.hdfcsky.com/api/kyc/v2/send-otp/sms",
    "headers": {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "origin": "https://hdfcsky.com",
        "referer": "https://hdfcsky.com/",
        "sec-ch-ua": "\"Not:A-Brand\";v=\"99\", \"Chromium\";v=\"120\", \"Google Chrome\";v=\"120\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "x-device-type": "web"
    },
    "json": {
        "phone_no": "91{phone}"
    }
},

# API 11
{
    "name": "Hoichoi",
    "method": "POST",
    "url": "https://prod-api.hoichoi.dev/core/api/v1/auth/signinup/code",
    "headers": {
        "content-type": "application/json",
        "rid": "anti-csrf",
        "st-auth-mode": "header"
    },
    "json": {
        "phoneNumber": "+91{phone}",
        "platform": "MOBILE_WEB"
    }
},

# API 12
{
    "name": "Hungama",
    "method": "POST",
    "url": "https://chcommunication.api.hungama.com/v1/communication/otp",
    "headers": {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.7",
        "alang": "en",
        "content-type": "application/json",
        "country_code": "IN",
        "identifier": "home",
        "mlang": "en",
        "origin": "https://www.hungama.com",
        "referer": "https://www.hungama.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "vlang": "en"
    },
    "json": {
        "mobileNo": "{phone}",
        "countryCode": "+91",
        "appCode": "un",
        "messageId": "1",
        "emailId": "",
        "subject": "Register",
        "priority": "1",
        "device": "web",
        "variant": "v1",
        "templateCode": 1
    }
},

# API 13
{
    "name": "Ixigo",
    "method": "PUT",
    "url": "https://www.ixigo.com/api/v4/oauth/signup",
    "headers": {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.8",
        "apikey": "ixiweb!2$",
        "clientid": "ixiweb",
        "content-type": "application/x-www-form-urlencoded",
        "deviceid": "33987b97d5de4e089461",
        "ixisrc": "ixiweb",
        "origin": "https://www.ixigo.com",
        "referer": "https://www.ixigo.com/login",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "uuid": "33987b97d5de4e089461",
        "x-requested-with": "XMLHttpRequest"
    },
    "cookies": {
        "session_id": "chxcwmxbahd",
        "_gcl_au": "1.1.1593170732.1766900446",
        "__cf_bm": "NL.67BE6_8MFfw9b2ZijAgKVu2fFPEo1tYTc4Dzmuvs-1772989668-1.0.1.1-7bGy.xxMBL8f7Kw9VWt1Rk._ETTjFCsK005p2P9eWn1u.XN4Cle4anoDYdh9Cf34fmEHOul0GWeqnvHZCXhIk1O2bDt_bCA0FXmif6xkAr0",
        "ixiUsrLocale": "urgn=-:ucnc=-:ucty=-:uctz=-:cnc=IN:cc=INR:lng=en",
        "ixiUID": "33987b97d5de4e089461",
        "ixiSrc": "WxStLj5WQl/M6yxaM5/tByHfRfJLF7dMLoMyhObxvTl2J1v1mhfjC7pHWOE3pH3nIZnVol+ODSAG9D1QIpj1bJAJiDQUAWGNQMZ5dkBwdZc=",
        "ixigoSrc": "33987b97d5de4e089461|REF-sear:08032026|REF-sear:08032026|REF-sear:08032026",
        "g_state": "{\"i_l\":0,\"i_ll\":1772989667503,\"i_b\":\"N3Q2caBFmOcZZxKSaE6elrvyX9hKpsiATJFfqwhyCu8\",\"i_e\":{\"enable_itp_optimization\":0}}"
    },
    "data": {
        "prefix": "+91",
        "name": "testuser",
        "phNo": "{phone}",
        "email": "{random_email}",
        "resendOnCall": "false",
        "key": "undefined",
        "platform": "Mobile"
    }
},

# API 14
{
    "name": "Jeep",
    "method": "POST",
    "url": "https://prod-jeep-api.one3d.in/api/v1/customer/send-otp",
    "headers": {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json",
        "authorization": "Bearer eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImltcmFuQGVjY2VudHJpY2VuZ2luZS5jb20iLCJpYXQiOjE3NzI5MTQ5NzgsImV4cCI6MTc3MzQzMzM3OH0.oMOQKi9QPEIAyGFNkyp55RpnsbEjTc6gNKQxMROv2N2dx3r-QmgWU7qOX1u5OpVSPFutI8ChYIKfmpddKA7G6w",
        "origin": "https://configurator.jeep-india.com",
        "referer": "https://configurator.jeep-india.com/",
        "user-agent": "Mozilla/5.0"
    },
    "json": {
        "mobile_number": "{phone}",
        "salutation": "Mr.",
        "first_name": "Test",
        "reg_source": "visualizer"
    }
},

# API 15
{
    "name": "RelianceRetail",
    "method": "POST",
    "url": "https://api.account.relianceretail.com/service/application/retail-auth/v2.0/send-otp",
    "headers": {
        "accept": "application/json",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyZXR1cm5fdWlfdXJsIjoid3d3Lmppb21hcnQuY29tL2N1c3RvbWVyL2FjY291bnQvbG9naW4_bXNpdGU9eWVzIiwiY2xpZW50X2lkIjoiZmRiNjQ2ZWEtZTcwOC00NzI1LWE5NTMtMjI4ZmExY2I4MzU1IiwiaWF0IjoxNzcyOTE2NzA0LCJzYWx0IjowfQ.Djfr8SBUQnBkj0UIb3hptBKoddGE0sIWniKDkB_oqFU",
        "origin": "https://account.relianceretail.com",
        "referer": "https://account.relianceretail.com/",
        "sec-ch-ua": "\"Not:A-Brand\";v=\"99\", \"Brave\";v=\"145\", \"Chromium\";v=\"145\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "source_meta": "{\"source_id\":null,\"device_fingerprint\":\"53d692cc-f822-4a-eyJwbGF0Zm9ybSI6\",\"os_name\":\"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36\",\"timestamp\":\"2026-03-07T20:51:54.003Z\"}"
    },
    "json": {
        "mobile": "{phone}"
    }
},

# API 16
{
    "name": "Khatabook",
    "method": "POST",
    "url": "https://api.khatabook.com/v1/auth/request-otp",
    "headers": {
        "accept": "*/*",
        "content-type": "application/json",
        "origin": "https://khatabook.com",
        "referer": "https://khatabook.com/",
        "user-agent": "Mozilla/5.0",
        "x-kb-app-locale": "en",
        "x-kb-app-name": "Khatabook Website",
        "x-kb-app-version": "000100",
        "x-kb-new-auth": "false",
        "x-kb-platform": "web"
    },
    "json": {
        "country_code": "+91",
        "phone": "{phone}",
        "app_signature": "Jc/Zu7qNqQ2"
    }
},

# API 17
{
    "name": "Klikk",
    "method": "POST",
    "url": "https://www.klikk.tv/?r=User/LoginWithOTP",
    "headers": {
        "accept": "application/json",
        "accept-language": "en-US,en;q=0.5",
        "api-key": "f4f068e71e0d87bf0ad51e6214ab84e9",
        "content-type": "application/json",
        "origin": "https://www.klikk.tv",
        "referer": "https://www.klikk.tv/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
    },
    "cookies": {
        "PHPSESSID": "0jujbjsdgfadp1rj4nh07m6jjn",
        "rzp_unified_session_id": "SOOnczW0oK2xdd",
        "promoBannerShown": "true"
    },
    "json": {
        "contactNumber": "+91-{phone}",
        "deviceName": "Chrome - Windows 10",
        "deviceType": 2,
        "socialType": 0
    }
},

# API 18
{
    "name": "KreditBee",
    "method": "PUT",
    "url": "https://api.kreditbee.in/v1/me/otp",
    "headers": {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.8",
        "authorization": "Bearer null",
        "content-type": "application/json",
        "origin": "https://pwa-web1.kreditbee.in",
        "referer": "https://pwa-web1.kreditbee.in/",
        "sec-ch-ua": "\"Not:A-Brand\";v=\"99\", \"Brave\";v=\"145\", \"Chromium\";v=\"145\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "x-kb-info": "eyJsYXQiOiIwIiwibG5nIjoiMCIsImRpZCI6IiIsImFwcHR5cGUiOiJ3ZWIiLCJhcHB2ZXIiOiIiLCJpc3Jvb3RlZCI6IiJ9"
    },
    "json": {
        "reason": "loginOrRegister",
        "mobile": "{phone}",
        "mediaSource": "",
        "firebaseInstanceId": "",
        "firebaseiosAppInstId": ""
    }
},

# API 19
{
    "name": "Kult",
    "method": "GET",
    "url": "https://api.kult.in/api/v2/otp/send",
    "headers": {
        "accept": "application/json, text/plain, */*",
        "bundle-identifier": "beauty.kult-beta.app",
        "device-type": "web",
        "origin": "https://www.kult.app",
        "referer": "https://www.kult.app/",
        "user-agent": "Mozilla/5.0"
    },
    "params": {
        "phone_number": "{phone}",
        "country_id": "106"
    }
},

# API 20
{
    "name": "LegalKart",
    "method": "POST",
    "url": "https://www.legalkart.com/api/v2/customer/register",
    "headers": {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json",
        "origin": "https://www.legalkart.com",
        "referer": "https://www.legalkart.com/consumer/",
        "user-agent": "Mozilla/5.0"
    },
    "cookies": {
        "id": "s:yfqotuDqouZWww8MqPrAs6bmaGJfDl0v.NlEl5sOGSrcw/pK4eRIeKoKcFtuD0x9Yx5P37Hmj294",
        "utm_source": "j:null"
    },
    "json": {
        "mobile": "{phone}",
        "country_code": 102,
        "device_fcm_id": "",
        "device": "web"
    }
},

# API 21
{
    "name": "Loan112",
    "method": "POST",
    "url": "https://www.loan112.com/login-sbm",
    "headers": {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "origin": "https://www.loan112.com",
        "referer": "https://www.loan112.com/apply-now",
        "x-requested-with": "XMLHttpRequest",
        "user-agent": "Mozilla/5.0"
    },
    "cookies": {
        "ci_session": "vv8d0b216regtl6k215j5upf5iausnro"
    },
    "data": {
        "mobile": "{phone}",
        "current_page": "login",
        "is_existing_customer": "2",
        "device_id": "91f015437a1ce3b818503dc2ecdf42c7"
    }
},

# API 22
{
    "name": "NatHabit",
    "method": "POST",
    "url": "https://authorize.api.nathabit.in/v2/auth/v2/otp/",
    "headers": {
        "accept": "*/*",
        "content-type": "application/json",
        "origin": "https://nathabit.in",
        "referer": "https://nathabit.in/",
        "user-agent": "Mozilla/5.0"
    },
    "json": {
        "phone": "{phone}",
        "send_on_whatsapp": False,
        "address_consent": True,
        "email": ""
    }
},

# API 23
{
    "name": "NatHabit",
    "method": "POST",
    "url": "https://authorize.api.nathabit.in/v2/auth/v2/otp/",
    "headers": {
        "accept": "*/*",
        "content-type": "application/json",
        "origin": "https://nathabit.in",
        "referer": "https://nathabit.in/",
        "user-agent": "Mozilla/5.0"
    },
    "json": {
        "phone": "{phone}",
        "send_on_whatsapp": True,
        "address_consent": True,
        "email": ""
    }
},

# API 24
{
    "name": "NoBroker",
    "method": "POST",
    "url": "https://www.nobroker.in/api/v3/account/otp/send",
    "headers": {
        "sec-ch-ua-platform": "\"Windows\"",
        "referer": "https://www.nobroker.in/",
        "sec-ch-ua": "\"Not:A-Brand\";v=\"99\", \"Brave\";v=\"145\", \"Chromium\";v=\"145\"",
        "sec-ch-ua-mobile": "?0",
        "baggage": "sentry-environment=production,sentry-release=1,sentry-public_key=7f77e36a137e48c209e1bd71cb221f3d,sentry-trace_id=2f20a69fd3ba46c0ada01c01a8635248",
        "sentry-trace": "2f20a69fd3ba46c0ada01c01a8635248-8f5a576a1c980766",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "accept": "*/*",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8"
    },
    "data": {
        "phone": "{phone}",
        "countryCode": "IN"
    }
},

# API 25
{
    "name": "Porter",
    "method": "POST",
    "url": "https://website-api-gateway-prod-ktor.porter.in/customer/onboarding/signup",
    "headers": {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.6",
        "brand": "smartshift",
        "client-request-uuid": "{uuid}",
        "content-type": "application/json",
        "country": "in",
        "origin": "https://porter.in",
        "preferred-language": "en",
        "referer": "https://porter.in/",
        "sec-gpc": "1",
        "source": "desktop_web",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
    },
    "json": {
        "mobile": "{phone}",
        "email": "{random_email}",
        "name": "{random_name}"
    }
},

# API 26
{
    "name": "Experian",
    "method": "POST",
    "url": "https://consumer.experian.in/ecv-jet/generic/generateOTP",
    "headers": {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://consumer.experian.in",
        "Referer": "https://consumer.experian.in/ecv-jet/signIn",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
    },
    "cookies": {
        "ecssessionprotector": "EED37E0165E66F43372C428A07ED438D",
        "SESSION_TRACKING_ID": "EED37E0165E66F43372C428A07ED438D"
    },
    "data": "{phone}~369"
},

# API 27
{
    "name": "RamFinCorp",
    "method": "POST",
    "url": "https://loans-api.ramfincorp.com/customers/customer-login-byMobile",
    "params": {
        "utm_source": "Organic",
        "mobile_no": "{phone}"
    },
    "json": {
        "mobile": "{phone}"
    }
},

# API 28
{
    "name": "SainaPlay",
    "method": "GET",
    "url": "https://vsms.mobiotics.com/prodv3/subscriberv2/v1/generateotp",
    "headers": {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.5",
        "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkZXZpY2VpZCI6IjEyNTI0NTMxMDI3ODU2MTciLCJkZXZpY2V0eXBlIjoiUEMiLCJkZXZpY2VvcyI6IldJTkRPV1MiLCJwcm92aWRlcmlkIjoic2FpbmFwbCIsInRpbWVzdGFtcCI6MTc3MjkwMTU5OSwiYXBwdmVyc2lvbiI6IjQ2LjQuMCIsImlwIjoiMTUuMTU4LjQyLjQ5IiwiR2VvTG9jSXAiOiI0OS40Ny4xOTQuMTYzIiwidmlzaXRpbmdjb3VudHJ5IjoiSU4iLCJpc3N1ZXIiOiJzYWluYXBsIiwiZXhwaXJlc0luIjo2MDQ4MDAsImlhdCI6MTc3MjkwMTYwMiwiZXhwIjoxNzczNTA2NDAyLCJpc3MiOiJzYWluYXBsIn0.aEIyiIf1dgBkDH_5crl1NEgjEc8unB01OJI3flsYGLk",
        "content-type": "application/json",
        "origin": "https://sainaplay.com",
        "referer": "https://sainaplay.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
    },
    "params": {
        "mobileno": "+91{phone}"
    }
},

# API 29
{
    "name": "Scripbox",
    "method": "POST",
    "url": "https://api.scripbox.com/auth/v1/user/session/otp/send",
    "headers": {
        "application-id": "ec3f64bd-5bfa-407c-9291-8cbda78c75a1",
        "x-app-name": "castor",
        "x-app-platform": "web",
        "content-type": "application/json"
    },
    "json": {
        "api_version": "1.0",
        "context": "send OTP",
        "data": {
            "attributes": {
                "scope": "login",
                "name": "User",
                "mobile_number": "{phone}"
            },
            "kind": "otp"
        }
    }
},

# API 30
{
    "name": "ShemarooMe",
    "method": "POST",
    "url": "https://www.shemaroome.com/users/mobile_no_signup",
    "headers": {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.7",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "origin": "https://www.shemaroome.com",
        "referer": "https://www.shemaroome.com/users/sign_in",
        "user-agent": "Mozilla/5.0",
        "x-requested-with": "XMLHttpRequest"
    },
    "cookies": {
        "theme_option": "light_theme"
    },
    "data": {
        "mobile_no": "+91{phone}",
        "registration_source": "organic"
    }
},

# API 31
{
    "name": "SwiggyPartner",
    "method": "GET",
    "url": "https://rms.swiggy.com/registration/otp-login/registration-status",
    "headers": {
        "accept": "application/json",
        "accept-language": "en-US,en;q=0.8",
        "content-type": "application/json",
        "origin": "https://partner.swiggy.com",
        "referer": "https://partner.swiggy.com/",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
    },
    "params": {
        "userId": "{phone}"
    }
},

# API 32
{
    "name": "SwiggyPartner",
    "method": "GET",
    "url": "https://rms.swiggy.com/registration/otp-login/registration-status",
    "headers": {
        "accept": "application/json",
        "content-type": "application/json",
        "origin": "https://partner.swiggy.com",
        "referer": "https://partner.swiggy.com/",
        "user-agent": "Mozilla/5.0"
    },
    "params": {
        "userId": "{phone}"
    }
},

# API 33
{
    "name": "TarangPlus",
    "method": "POST",
    "url": "https://tarangplus.in/users/sign_up",
    "headers": {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.5",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "origin": "https://tarangplus.in",
        "referer": "https://tarangplus.in/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
    },
    "cookies": {
        "_oriya_tv_session": "jOxwTbjH7Hgl9IOwTKNwETySUgYKIWVX34QmypOMUkNqOF3tEQXetTRO4BKzBCXhzOANr2Ga6sdKuTsK50tAbqwgGG1jvHetceMFNqEeQ1XVxXqu6kQrdY6OXfN1QueNY1+BTZZ0Oioo8jOaV08=--x/LgokYEREfquC4s--HUmPdEDAuA9PXGX1SoM9DQ==",
        "G_ENABLED_IDPS": "google"
    },
    "data": {
        "name": "test user",
        "email_id": "{random_email}",
        "mobile_no": "{phone}",
        "type": "phone",
        "password": "{random_password}"
    }
},

# API 34
{
    "name": "Truecaller",
    "method": "POST",
    "url": "https://asia-south1-truecaller-web.cloudfunctions.net/webapi/noneu/auth/truecaller/v1/send-otp",
    "headers": {
        "accept": "application/json",
        "content-type": "application/json",
        "origin": "https://www.truecaller.com",
        "referer": "https://www.truecaller.com/",
        "user-agent": "Mozilla/5.0"
    },
    "json": {
        "phone": "91{phone}",
        "countryCode": "in"
    }
},

# API 35
{
    "name": "Uber",
    "method": "POST",
    "url": "https://auth.uber.com/v2/submit-form",
    "headers": {
        "accept": "*/*",
        "content-type": "application/json",
        "origin": "https://auth.uber.com",
        "referer": "https://auth.uber.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "x-csrf-token": "x",
        "x-uber-client-name": "usl_desktop"
    },
    "json": {
        "formContainerAnswer": {
            "formAnswer": {
                "flowType": "INITIAL",
                "standardFlow": True,
                "screenAnswers": [
                    {
                        "screenType": "PHONE_NUMBER_INITIAL",
                        "eventType": "TypeInputMobile",
                        "fieldAnswers": [
                            {
                                "fieldType": "PHONE_COUNTRY_CODE",
                                "phoneCountryCode": "+91"
                            },
                            {
                                "fieldType": "PHONE_NUMBER",
                                "phoneNumber": "{phone}"
                            }
                        ]
                    }
                ]
            }
        }
    }
},

# API 36
{
    "name": "Watcho",
    "method": "POST",
    "url": "https://dishtv-api.revlet.net/service/api/auth/get/otp",
    "headers": {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json",
        "box-id": "9bf5ea6a-17e9-730f-ae3c-dff5de0743d7",
        "session-id": "a935783b-c153-4854-af3f-13325ad298f6",
        "tenant-code": "dishtv",
        "origin": "https://www.watcho.com",
        "user-agent": "Mozilla/5.0"
    },
    "json": {
        "mobile": "91{phone}",
        "context": "login"
    }
},

# API 37
{
    "name": "ZEE5",
    "method": "POST",
    "url": "https://auth.zee5.com/v1/user/sendotp",
    "headers": {
        "accept": "application/json",
        "accept-language": "en-US,en;q=0.5",
        "content-type": "application/json",
        "device_id": "c3b10458-2ea8-42fe-85f8-241025df0ea6",
        "esk": "YzNiMTA0NTgtMmVhOC00MmZlLTg1ZjgtMjQxMDI1ZGYwZWE2X19nQlFhWkxpTmRHTjlVc0NLWmFsb2doejl0OVN0V0xTRF9fMTc3MjkwNDk4NjE3Mw==",
        "origin": "https://www.zee5.com",
        "referer": "https://www.zee5.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "x-z5-guest-token": "c3b10458-2ea8-42fe-85f8-241025df0ea6"
    },
    "json": {
        "phoneno": "91{phone}"
    }
}

]