//Kanged from https://github.com/libDrive/cloudflare/blob/main/index.js

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
