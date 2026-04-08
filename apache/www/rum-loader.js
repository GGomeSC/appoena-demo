(function loadDdRumSdk() {
  const ddRumConfig = window.APP_CONFIG && window.APP_CONFIG.ddRum;
  const site = ddRumConfig && ddRumConfig.site;
  const applicationId = ddRumConfig && ddRumConfig.applicationId;
  const clientToken = ddRumConfig && ddRumConfig.clientToken;

  if (!site || !applicationId || !clientToken) {
    window.dispatchEvent(new Event("dd-rum-ready"));
    return;
  }

  const siteMap = {
    "datadoghq.com": "us1",
    "us3.datadoghq.com": "us3",
    "us5.datadoghq.com": "us5",
    "datadoghq.eu": "eu",
    "ap1.datadoghq.com": "ap1",
    "ap2.datadoghq.com": "ap2",
    "ddog-gov.com": "us1-fed",
  };

  const siteKey = site.toLowerCase();
  const sitePath = siteMap[siteKey] || "us1";
  const script = document.createElement("script");

  script.src = `https://www.datadoghq-browser-agent.com/${sitePath}/v6/datadog-rum.js`;
  script.async = false;
  script.onload = function onLoad() {
    window.dispatchEvent(new Event("dd-rum-ready"));
  };
  script.onerror = function onError() {
    window.dispatchEvent(new Event("dd-rum-ready"));
  };

  document.head.appendChild(script);
})();
