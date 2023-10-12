const JSEncrypt = require('node-jsencrypt'); // npm install node-jsencrypt
const CryptoJS = require('crypto-js'); // npm install crypto-js

var $publicKey = '-----BEGIN PUBLIC KEY-----\n\
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA0zI8aibR9ZN57QObFxvI\n\
wiRTmELItVVBLMrLd71ZqakR6oWUKkcAGgmxad2TCy3UeRe4A0Dduw97oXlbl5rK\n\
RGISzpLO8iMSYtsim5aXZX9SB5x3S9ees4CZ6MYD/4XQOTrU0r1TMT6wXlhVvwNb\n\
fMNYHm3vkY0rhfxBCVPFJoHjAGDFWNCAhf4KfalfvWsGL32p8N/exG2S4yXVHuV6\n\
cHDyFJAItKVmyuTmB62pnPs5KvNv6oPmtmhMxxsvBOyh7uLwB5TonxtZpWZ3A1wf\n\
43ByuU7F3qGnFqL0GeG/JuK+ZR40LARyevHy9OZ5pMa0Nwqb8PwfK810Bc8PxD8N\n\
EwIDAQAB\n\
-----END PUBLIC KEY-----\n\
';
var encryptPassChars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXTZabcdefghiklmnopqrstuvwxyz*&-%/!?*+=()";
var rsaEncrypt = new JSEncrypt();
rsaEncrypt.setPublicKey($publicKey);
var keyEncrypt = function(data) {
	var passPhrase = generateEncryptPassword(32);

	var iv = CryptoJS.lib.WordArray.random(128/8).toString(CryptoJS.enc.Hex);
	var salt = CryptoJS.lib.WordArray.random(128/8).toString(CryptoJS.enc.Hex);
	var key = CryptoJS.PBKDF2(
		passPhrase, 
		CryptoJS.enc.Hex.parse(salt),
		{ keySize: 128/32, iterations: 1000 });

	var aesEncrypted = CryptoJS.AES.encrypt(data, key, { iv: CryptoJS.enc.Hex.parse(iv) });
	var aesKey = passPhrase + ":::" + salt + ":::" + aesEncrypted.iv;
	var encryptedMessage = aesEncrypted.ciphertext.toString(CryptoJS.enc.Base64);
	var encryptedKey = rsaEncrypt.encrypt(aesKey);

	var encrypted = encryptedKey + ":::" + encryptedMessage;
	return encrypted;
};

var generateEncryptPassword = function (length) {
	var randomstring = '';
	for (var i = 0; i < length; i++) {
		var rnum = Math.floor(Math.random() * encryptPassChars.length);
		randomstring += encryptPassChars.substring(rnum, rnum + 1);
	}
	return randomstring;
};



