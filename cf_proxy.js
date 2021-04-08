/* 
Sources:

1. https://github.com/libDrive/cloudflare/blob/main/index.js
2. https://github.com/alx-xlx/goindex/blob/master/goindex.js

MIT License

Copyright (c) 2021 libDrive

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

var authConfig = {
	"client_id": "202264815644.apps.googleusercontent.com", // client_id from token string
	"client_secret": "X4Z3ca8xfWDb1Voo-F9a7ZxJ", // client_secret from token string
	"refresh_token": "*******" // refresh token from token string
};
addEventListener("fetch", (event) => {
	event.respondWith(handleRequest(event.request));
});
async function handleRequest(request) {
	const drive = new googleDrive(authConfig);
	let url = new URL(request.url);
	let path = url.pathname;
	if(path.startsWith("/load")) {
		var file_id = path.split("/").pop();
		return drive.downloadAPI(request.headers.get("Range"), file_id);
	} else {
		return new Response(null, {
			"status": 404
		});
	}
}
class googleDrive {
	constructor(authConfig) {
		this.authConfig = authConfig;
		this.accessToken();
	}
	async downloadAPI(range = "", file_id) {
		const access_token = await this.accessToken();
		let requestOption = {
			method: "GET",
			headers: {
				Authorization: `Bearer ${access_token}`,
				Range: range
			},
		};
		let url = `https://www.googleapis.com/drive/v3/files/${file_id}?alt=media`;
		let resp = await fetch(url, requestOption);
		let {
			headers
		} = (resp = new Response(resp.body, resp));
		headers.append("Access-Control-Allow-Origin", "*");
		headers.set("Content-Disposition", "inline");
		headers.set("Access-Control-Allow-Headers", "*")
		return resp;
	}
	async accessToken() {
		console.log("accessToken");
		if(this.authConfig.expires == undefined || this.authConfig.expires < Date.now()) {
			const obj = await this.fetchAccessToken();
			if(obj.access_token != undefined) {
				this.authConfig.accessToken = obj.access_token;
				this.authConfig.expires = Date.now() + 3500 * 1000;
			}
		}
		return this.authConfig.accessToken;
	}
	async fetchAccessToken() {
		console.log("fetchAccessToken");
		const url = "https://www.googleapis.com/oauth2/v4/token";
		const headers = {
			'Content-Type': 'application/x-www-form-urlencoded'
		};
		const post_data = {
			'client_id': this.authConfig.client_id,
			'client_secret': this.authConfig.client_secret,
			'refresh_token': this.authConfig.refresh_token,
			'grant_type': 'refresh_token'
		}
		let requestOption = {
			'method': 'POST',
			'headers': headers,
			'body': this.enQuery(post_data)
		};
		const response = await fetch(url, requestOption);
		return await response.json();
	}
	enQuery(data) {
		const ret = [];
		for(let d in data) {
			ret.push(encodeURIComponent(d) + '=' + encodeURIComponent(data[d]));
		}
		return ret.join('&');
	}
}