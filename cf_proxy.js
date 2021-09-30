var credentials = {
  "client_id": "202264815644.apps.googleusercontent.com", // rclone client_id
  "client_secret": "X4Z3ca8xfWDb1Voo-F9a7ZxJ", // rclone client_secret
  "refresh_token": "*******" // refresh token is unique
}

async function handleRequest(request) {
  const drive = new gdrive(credentials)
  let url = new URL(request.url)
  let path_split = url.pathname.split('/')
  if (path_split[1] == 'load') {
    var file_id = path_split[2]
    var file_name = path_split[3] || 'file_name.vid'
    return drive.streamFile(request.headers.get("Range"), file_id, file_name)
  }
  else if (url.pathname == '/')
      return new Response('200 Online!', { "status": 200 })
  else
      return new Response('404 Not Found!', { "status": 404 })
}

class gdrive {
  constructor(credentials) {
    this.gapihost = 'https://www.googleapis.com'
    this.credentials = credentials
  }
  async streamFile(range = "", file_id, file_name) {
    //console.log(`streamFile: ${file_id}, range: ${range}`)
    let fetchURL = `${this.gapihost}/drive/v3/files/${file_id}?alt=media`
    let fetchData = await this.authData()
    fetchData.headers['Range'] = range
    let streamResp = await fetch(fetchURL, fetchData)
    let { readable, writable } = new TransformStream()
    streamResp.body.pipeTo(writable)
    return new Response(readable, streamResp)
  }
  async accessToken() {
    //console.log("accessToken")
    if (!this.credentials.token || this.credentials.token.expires_in < Date.now()) {
      this.credentials.token = await this.fetchAccessToken()
      this.credentials.token.expires_in = Date.now() + this.credentials.token.expires_in * 1000
    }
    return this.credentials.token.access_token
  }
  async fetchAccessToken(url = `${this.gapihost}/oauth2/v4/token`) {
    //console.log("fetchAccessToken")
    let jsonBody = {
      'client_id': this.credentials.client_id,
      'client_secret': this.credentials.client_secret,
      'refresh_token': this.credentials.refresh_token,
      'grant_type': 'refresh_token'
    }
    let response = await fetch(url, { method: 'POST', body: JSON.stringify(jsonBody) })
    return await response.json()
  }
  async authData(headers = {}) {
    headers['Authorization'] = `Bearer ${await this.accessToken()}`;
    return { 'method': 'GET', 'headers': headers }
  }
}

addEventListener("fetch", (event) => {
  event.respondWith(handleRequest(event.request))
})
