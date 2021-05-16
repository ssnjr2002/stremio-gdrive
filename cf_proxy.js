var authConfig = {
	"client_id": "202264815644.apps.googleusercontent.com", // rclone client_id
	"client_secret": "X4Z3ca8xfWDb1Voo-F9a7ZxJ", // rclone client_secret
	"refresh_token": "*******" // refresh token is unique
};
addEventListener("fetch", (event) => {
	event.respondWith(handleRequest(event.request));
});
async function handleRequest(request) {
	const drive = new gdrive(authConfig);
	let url = new URL(request.url);
	let path = url.pathname;
	if(path.startsWith("/load")) {
		var file_id = path.split("/").pop();
		return drive.streamFile(request.headers.get("Range"), file_id);
	} else {
		return new Response(null, {
			"status": 200
		});
	}
}
class gdrive {
  constructor(authConfig) {
    this.gapihost = 'https://www.googleapis.com'
    this.authConfig = authConfig
  }
  async streamFile(range = "", file_id) {
    console.log(`streamFile: ${file_id}, range: ${range}`)
    let streamResp = await fetch(`${this.gapihost}/drive/v3/files/${file_id}?alt=media`, {
      method: "GET",
      headers: {Authorization: `Bearer ${await this.accessToken()}`, Range: range}
    })
    let { readable, writable } = new TransformStream()
    streamResp.body.pipeTo(writable)
    return new Response(readable, streamResp)
  }
  async accessToken() {
    console.log("accessToken")
    if(!this.authConfig.oauth || this.authConfig.expires < Date.now()) {
      this.authConfig.oauth = await this.fetchAccessToken()
      this.authConfig.oauth.expires_in = Date.now() + this.authConfig.oauth.expires_in * 1000
    }
    return this.authConfig.oauth.access_token
  }
  async fetchAccessToken() {
    console.log("fetchAccessToken")
    let response = await fetch(`${this.gapihost}/oauth2/v4/token`, {
      method: 'POST',
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: this.enQuery({
          'client_id': this.authConfig.client_id,
          'client_secret': this.authConfig.client_secret,
          'refresh_token': this.authConfig.refresh_token,
          'grant_type': 'refresh_token'
        })
    })
	console.log(await tgnotify(JSON.stringify("fetchAccessToken " + Date())))
    return await response.json()
  }
  // Source: https://github.com/alx-xlx/goindex/blob/master/goindex.js#L311
  enQuery(data) {
    const ret = []
    for(let d in data) {
      ret.push(encodeURIComponent(d) + '=' + encodeURIComponent(data[d]))
    }
    return ret.join('&')
  }
}
