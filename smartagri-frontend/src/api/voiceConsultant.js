import API from './axios';

export const getLanguages = async () => {
  const res = await API.get('/api/voice-consultant/languages');
  return res.data;
};

export const prefetchLanguages = async (langCode) => {
  const res = await API.post('/api/voice-consultant/prefetch', { lang_code: langCode });
  return res.data;
};

export const voiceConverse = async (audioBase64, langCode, profile, isComprehensive = false, text = '') => {
  const res = await API.post('/api/voice-consultant/converse', {
    audio: audioBase64,
    text,
    lang_code: langCode,
    profile,
    is_comprehensive: isComprehensive
  });
  return res.data;
};

export const textAsk = async (question, profile, isComprehensive = false) => {
  const res = await API.post('/api/voice-consultant/ask', {
    question,
    profile,
    is_comprehensive: isComprehensive
  });
  return res.data;
};

export const textToSpeech = async (text, langCode) => {
  const res = await API.post('/api/voice-consultant/speak', {
    text,
    lang_code: langCode
  });
  return res.data;
};

export const checkBleu = async (reference, candidate) => {
  const res = await API.post('/api/voice-consultant/bleu', {
    reference,
    candidate
  });
  return res.data;
};

export const voiceDiagnose = async (imageB64, langCode, cropContext = '') => {
  const res = await API.post('/api/voice-consultant/voice-diagnose', {
    image: imageB64,
    lang_code: langCode,
    crop_context: cropContext
  });
  return res.data;
};

export const voiceMarketQuery = async (audioBase64, langCode) => {
  const res = await API.post('/api/voice-consultant/voice-market', {
    audio: audioBase64,
    lang_code: langCode
  });
  return res.data;
};

export const voiceWeatherQuery = async (audioBase64, langCode, lat = 13.0827, lon = 80.2707) => {
  const res = await API.post('/api/voice-consultant/voice-weather', {
    audio: audioBase64,
    lang_code: langCode,
    lat,
    lon
  });
  return res.data;
};

export const getSubsidies = async (state, crop = '', farmSize = '') => {
  const res = await API.get(`/api/subsidies/${state}`, {
    params: { crop, farm_size: farmSize }
  });
  return res.data;
};

export const getNaturalFarmingTechniques = async () => {
  const res = await API.get('/api/natural-farming/techniques');
  return res.data;
};

export const getNaturalFarmingStrategies = async () => {
  const res = await API.get('/api/natural-farming/strategies');
  return res.data;
};

export const generateNaturalFarmingPlan = async () => {
  const res = await API.post('/api/natural-farming/plan');
  return res.data;
};
