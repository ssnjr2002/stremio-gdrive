/* Kanged from https://github.com/libDrive/cloudflare/blob/main/index.js

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

// Copy all the stuff below this line for the CF proxy worker.

addEventListener("fetch", (event) => {
    event.respondWith(handleRequest(event.request));
  });

  async function handleRequest(request) {
    const drive = new googleDrive();
    let url = new URL(request.url);
    let path = url.pathname;
    if (path.startsWith("/load")) {
        const session = JSON.parse(atob(url.searchParams.get("session")));
        return drive.downloadAPI(
          request.headers.get("Range"),
          session.access_token,
          session.file_id
      );
    } else {
        return new Response(null, {"status" : 404});
    }
  }

  class googleDrive {
    async downloadAPI(range = "", access_token, file_id) {
        let requestOption = {
          method: "GET",
          headers: { Authorization: `Bearer ${access_token}`, Range: range },
        };
        let url = `https://www.googleapis.com/drive/v3/files/${file_id}?alt=media`;
        let resp = await fetch(url, requestOption);
        let { headers } = (resp = new Response(resp.body, resp));
        headers.append("Access-Control-Allow-Origin", "*");
        headers.set("Content-Disposition", "inline");
        headers.set("Access-Control-Allow-Headers", "*")
        return resp;
    }
  }
