/*
 *   Редактор JWT. Все вычисления локальные, прямо в браузере
 */


/*
 *   Проверка подписи по (n,e)
 */

function createPublicKey(e, n) {
    const modulusHex = n.toString(16).padStart(256, '0');
    const exponentHex = e.toString(16).padStart(4, '0');

    return KEYUTIL.getKey({
        n: modulusHex,
        e: exponentHex
    });
}

function verifyJWT(token, e, n) {
    try {
        const publicKeyRsa = createPublicKey(e, n);
        console.log('Verifying token: e='+e.toString()+' n='+n.toString())
        const isValid = KJUR.jws.JWS.verifyJWT(token, publicKeyRsa, {alg: ['RS256']});
        console.log('isValid = '+isValid.toString())
        return isValid;
    } catch (err) {
        showPopup('Ошибка проверки подписи. Некорректные параметры');
        console.error('Token verification failed:', err.message);
        return false;
    }
}

/*
 *   Подпись токена по (n,d)
 */

function createPrivateKey(d, n) {
    const modulusHex = n.toString(16).padStart(256, '0');
    const exponentHex = d.toString(16).padStart(256, '0');
    const publicExpHex = "010001";  // e=65537 захардкожено везде

    return KEYUTIL.getKey({
        n: modulusHex,
        d: exponentHex,
        e: publicExpHex
    });
}

function signJWT(payload, d, n) {
    try {
        const privateKeyRsa = createPrivateKey(d, n);
        const header = { alg: 'RS256', typ: 'JWT' };
        const jwtHeader = JSON.stringify(header);
        const jwtPayload = JSON.stringify(payload);
        return KJUR.jws.JWS.sign('RS256', jwtHeader, jwtPayload, privateKeyRsa);
    } catch (err) {
        console.error('Token signature failed:', err.message);
        return null;
    }
}

/*
 *   Ивенты на кнопках
 */

$(document).ready(function() {
    if (!!$.cookie('token')) {
        document.getElementById('token').value = $.cookie('token');
    }

    document.getElementById('fetchParams').addEventListener('click', () => {
        $.ajax({
            type: 'GET',
            url: '/api/jwt/verify?publicKey=1',
            success: function(response, textStatus, jqXHR) {
                if (jqXHR.status === 200) {
                    document.getElementById('e').value = response['jwt_public_key']['e'];
                    document.getElementById('n').value = response['jwt_public_key']['n'];
                }
            },
            error: function(jqXHR) {
                const message = jqXHR.responseJSON.message || 'Произошла ошибка. Попробуйте перелогиниться';
                showPopup(message);
            }
        });
    });

    document.getElementById('verifyToken').addEventListener('click', () => {
        const token = document.getElementById('token').value;
        const e = BigInt(document.getElementById('e').value);
        const n = BigInt(document.getElementById('n').value);

        const isValid = verifyJWT(token, e, n);
        const banner = document.getElementById('banner');

        if (isValid) {
            banner.textContent = 'Подпись валидная!';
            banner.className = 'banner green';
        } else {
            banner.textContent = 'Некорректная подпись';
            banner.className = 'banner red';
        }
        banner.style.display = 'block';
    });

    document.getElementById('signToken').addEventListener('click', () => {
        const payload = JSON.parse(document.getElementById('payload').value);
        const d = BigInt(document.getElementById('d').value);
        const n = BigInt(document.getElementById('signN').value);

        const signedToken = signJWT(payload, d, n);

        if (signedToken) {
            document.getElementById('result').value = signedToken;
        } else {
            document.getElementById('result').value = 'Ошибка создания токена.';
        }
    });

});

