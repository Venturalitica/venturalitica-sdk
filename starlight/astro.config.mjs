import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import starlightLlmsTxt from 'starlight-llms-txt';

export default defineConfig({
  site: 'https://venturalitica.github.io/venturalitica-sdk',
  base: '/venturalitica-sdk',
  integrations: [
    starlight({
      title: {
        en: 'Venturalítica',
        es: 'Venturalítica',
      },
      description: 'The Glass Box for High-Risk AI. Turn your Python code into Legal Evidence.',
      head: [
        {
          tag: 'script',
          content: `!function(t,e){var o,n,p,r;e.__SV||(window.posthog=e,e._i=[],e.init=function(i,s,a){function g(t,e){var o=e.split(".");2==o.length&&(t=t[o[0]],e=o[1]),t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}(p=t.createElement("script")).type="text/javascript",p.crossOrigin="anonymous",p.async=!0,p.src=s.api_host.replace(".i.posthog.com","-assets.i.posthog.com")+"/static/array.js",(r=t.getElementsByTagName("script")[0]).parentNode.insertBefore(p,r);var u=e;for(void 0!==a?u=e[a]=[]:a="posthog",u.people=u.people||[],u.toString=function(t){var e="posthog";return"posthog"!==a&&(e+="."+a),t||(e+=" (stub)"),e},u.people.toString=function(){return u.toString(1)+".people (stub)"},o="init capture register register_once register_for_session unregister unregister_for_session getFeatureFlag getFeatureFlagPayload isFeatureEnabled reloadFeatureFlags updateEarlyAccessFeatureEnrollment getEarlyAccessFeatures on onFeatureFlags onSessionId getSurveys getActiveMatchingSurveys renderSurvey canRenderSurvey getNextSurveyStep identify setPersonProperties group resetGroups setPersonPropertiesForFlags resetPersonPropertiesForFlags setGroupPropertiesForFlags resetGroupPropertiesForFlags reset get_distinct_id getGroups get_session_id get_session_replay_url alias set_config startSessionRecording stopSessionRecording sessionRecordingStarted captureException loadToolbar get_property getSessionProperty createPersonProfile opt_in_capturing opt_out_capturing has_opted_in_capturing has_opted_out_capturing clear_opt_in_out_capturing debug getPageviewId".split(" "),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])},e.__SV=1)}(document,window.posthog||[]);posthog.init('phc_ExGZUlLBLUyI6pHKaBFWdekgDF0mFeDYWyFOwffOjWe',{api_host:'https://eu.i.posthog.com',persistence:'memory',property_denylist:['$ip']});`,
        },
      ],
      logo: {
        src: './src/assets/logo.svg',
      },
      favicon: '/favicon.svg',
      social: [
        { icon: 'github', label: 'GitHub', href: 'https://github.com/venturalitica/venturalitica-sdk' },
      ],
      defaultLocale: 'root',
      locales: {
        root: {
          label: 'English',
          lang: 'en',
        },
        es: {
          label: 'Español',
          lang: 'es',
        },
        pt: {
          label: 'Português',
          lang: 'pt',
        },
      },
      sidebar: [
        {
          label: 'Getting Started',
          translations: { es: 'Primeros Pasos', pt: 'Introdução' },
          items: [
            { slug: 'quickstart' },
            { slug: 'full-lifecycle' },
          ],
        },
        {
          label: 'Academy',
          translations: { es: 'Academia', pt: 'Academia' },
          items: [
            { slug: 'academy' },
            { slug: 'academy/level1-policy' },
            { slug: 'academy/level2-integrator' },
            { slug: 'academy/level3-auditor' },
            { slug: 'academy/level4-annex-iv' },
          ],
        },
        {
          label: 'Guides',
          translations: { es: 'Guías', pt: 'Guias' },
          items: [
            { slug: 'guides/policy-authoring' },
            { slug: 'guides/dashboard' },
            { slug: 'guides/column-binding' },
            { slug: 'guides/compliance-mapping' },
            { slug: 'guides/experimental' },
          ],
        },
        {
          label: 'Tutorials',
          translations: { es: 'Tutoriales', pt: 'Tutoriais' },
          items: [
            { slug: 'tutorials/writing-policy' },
          ],
        },
        {
          label: 'Reference',
          translations: { es: 'Referencia', pt: 'Referência' },
          items: [
            { slug: 'reference/api' },
            { slug: 'reference/metrics' },
            { slug: 'reference/probes' },
            { slug: 'reference/multiclass-fairness' },
          ],
        },
      ],
      plugins: [
        starlightLlmsTxt(),
      ],
      customCss: ['./src/styles/custom.css'],
    }),
  ],
});
