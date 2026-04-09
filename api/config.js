export default function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  res.json({
    chatUrl: process.env.CHAT_BACKEND || '',
  });
}
