import React, { useEffect, useState } from 'react';
import { apiClient } from '../api/client';

const S: Record<string, React.CSSProperties> = {
  root: { maxWidth: 640, margin: '0 auto', padding: 24 },
  card: {
    background: '#1a1a2e',
    border: '1px solid #2d2d44',
    borderRadius: 8,
    padding: 24,
    marginBottom: 24,
  },
  title: { fontSize: 16, fontWeight: 700, color: '#e0e0f0', marginBottom: 4 },
  divider: { border: 'none', borderTop: '1px solid #2d2d44', margin: '16px 0' },
  instructions: { color: '#8888aa', fontSize: 13, lineHeight: 1.7, marginBottom: 16 },
  code: {
    background: '#0d0d1a',
    border: '1px solid #2d2d44',
    borderRadius: 4,
    padding: '2px 6px',
    fontFamily: 'monospace',
    fontSize: 12,
    color: '#a0a0ff',
  },
  label: { display: 'block', fontSize: 13, color: '#8888aa', marginBottom: 4 },
  input: {
    width: '100%',
    background: '#0d0d1a',
    border: '1px solid #2d2d44',
    borderRadius: 4,
    color: '#e0e0f0',
    padding: '8px 10px',
    fontSize: 13,
    fontFamily: 'monospace',
    boxSizing: 'border-box',
    marginBottom: 12,
  },
  row: { display: 'flex', gap: 8, marginTop: 4 },
  btn: {
    padding: '8px 18px',
    borderRadius: 4,
    border: 'none',
    cursor: 'pointer',
    fontSize: 13,
    fontWeight: 600,
  },
  btnPrimary: { background: '#4040cc', color: '#fff' },
  btnSecondary: { background: '#2d2d44', color: '#e0e0f0' },
  btnCopy: { background: '#2d2d44', color: '#e0e0f0', fontSize: 12 },
  status: { marginTop: 12, fontSize: 13, padding: '8px 12px', borderRadius: 4 },
  statusOk: { background: '#0d2b1a', color: '#4caf82', border: '1px solid #2d5a3a' },
  statusErr: { background: '#2b0d0d', color: '#ff6666', border: '1px solid #5a2d2d' },
  codeBlock: {
    background: '#0d0d1a',
    border: '1px solid #2d2d44',
    borderRadius: 4,
    padding: '10px 14px',
    fontFamily: 'monospace',
    fontSize: 12,
    color: '#a0a0ff',
    whiteSpace: 'pre',
    overflowX: 'auto',
    marginBottom: 8,
  },
  sectionTitle: { fontSize: 14, fontWeight: 700, color: '#e0e0f0', marginBottom: 12 },
};

export default function NotificationsView() {
  const [token, setToken] = useState('');
  const [chatId, setChatId] = useState('');
  const [masked, setMasked] = useState('');
  const [tokenSet, setTokenSet] = useState(false);
  const [saveStatus, setSaveStatus] = useState<{ ok: boolean; msg: string } | null>(null);
  const [testStatus, setTestStatus] = useState<{ ok: boolean; msg: string } | null>(null);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [cronCopied, setCronCopied] = useState(false);

  useEffect(() => {
    apiClient.getNotificationConfig().then((cfg) => {
      setTokenSet(cfg.bot_token_set);
      setMasked(cfg.bot_token_masked);
      setChatId(cfg.chat_id);
    }).catch(() => {});
  }, []);

  const handleSave = async () => {
    if (!token && !chatId) return;
    setSaving(true);
    setSaveStatus(null);
    try {
      const cfg = await apiClient.saveNotificationConfig({ bot_token: token, chat_id: chatId });
      setTokenSet(cfg.bot_token_set);
      setMasked(cfg.bot_token_masked);
      setChatId(cfg.chat_id);
      setToken('');
      setSaveStatus({ ok: true, msg: 'Configuration saved.' });
    } catch {
      setSaveStatus({ ok: false, msg: 'Failed to save configuration.' });
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    setTestStatus(null);
    try {
      await apiClient.sendTestNotification();
      setTestStatus({ ok: true, msg: 'Test message sent! Check your Telegram.' });
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Failed to send test message.';
      setTestStatus({ ok: false, msg });
    } finally {
      setTesting(false);
    }
  };

  const cronLine = `0 9 * * 1-5  cd /path/to/app && python3 scripts/send_report.py >> logs/report.log 2>&1`;

  const handleCopyCron = () => {
    navigator.clipboard.writeText(cronLine).then(() => {
      setCronCopied(true);
      setTimeout(() => setCronCopied(false), 2000);
    });
  };

  return (
    <div style={S.root}>
      {/* ── Bot setup ── */}
      <div style={S.card}>
        <div style={S.title}>Telegram Bot Setup</div>
        <hr style={S.divider} />

        <p style={S.instructions}>
          1. Message <code style={S.code}>@BotFather</code> on Telegram → <code style={S.code}>/newbot</code> → copy the token.<br />
          2. Start your bot: open the bot chat and send <code style={S.code}>/start</code>.<br />
          3. Get your chat ID: after starting the bot, visit<br />
          &nbsp;&nbsp;&nbsp;<code style={S.code}>https://api.telegram.org/bot{'<TOKEN>'}/getUpdates</code><br />
          &nbsp;&nbsp;&nbsp;and look for <code style={S.code}>message.chat.id</code> in the response.
        </p>

        <label style={S.label}>Bot Token {tokenSet && <span style={{ color: '#4caf82' }}>({masked})</span>}</label>
        <input
          style={S.input}
          type="password"
          placeholder={tokenSet ? 'Enter new token to update…' : 'Paste token from @BotFather'}
          value={token}
          onChange={(e) => setToken(e.target.value)}
        />

        <label style={S.label}>Chat ID</label>
        <input
          style={S.input}
          type="text"
          placeholder="e.g. 987654321"
          value={chatId}
          onChange={(e) => setChatId(e.target.value)}
        />

        <div style={S.row}>
          <button style={{ ...S.btn, ...S.btnPrimary }} onClick={handleSave} disabled={saving}>
            {saving ? 'Saving…' : 'Save ✓'}
          </button>
          <button style={{ ...S.btn, ...S.btnSecondary }} onClick={handleTest} disabled={testing || !tokenSet}>
            {testing ? 'Sending…' : 'Send Test ▶'}
          </button>
        </div>

        {saveStatus && (
          <div style={{ ...S.status, ...(saveStatus.ok ? S.statusOk : S.statusErr) }}>
            {saveStatus.msg}
          </div>
        )}
        {testStatus && (
          <div style={{ ...S.status, ...(testStatus.ok ? S.statusOk : S.statusErr) }}>
            {testStatus.msg}
          </div>
        )}
      </div>

      {/* ── Cron setup ── */}
      <div style={S.card}>
        <div style={S.title}>Cron Setup (VPS)</div>
        <hr style={S.divider} />

        <p style={S.instructions}>
          Run <code style={S.code}>crontab -e</code> on your VPS, then add one of the lines below.
          Make sure your <code style={S.code}>.env</code> file contains{' '}
          <code style={S.code}>TELEGRAM_BOT_TOKEN</code> and <code style={S.code}>TELEGRAM_CHAT_ID</code>.
        </p>

        <div style={S.sectionTitle}>Daily at 9am Mon–Fri</div>
        <div style={S.codeBlock}>{cronLine}</div>
        <button style={{ ...S.btn, ...S.btnCopy }} onClick={handleCopyCron}>
          {cronCopied ? 'Copied ✓' : 'Copy'}
        </button>

        <hr style={S.divider} />

        <div style={S.sectionTitle}>Hourly (market hours 9am–4pm Mon–Fri)</div>
        <div style={S.codeBlock}>
          {'0 9-16 * * 1-5  cd /path/to/app && python3 scripts/send_report.py >> logs/report.log 2>&1'}
        </div>
        <p style={{ ...S.instructions, marginBottom: 0 }}>
          Run <code style={S.code}>bash scripts/setup_cron.sh</code> locally to print lines with the correct absolute path.
        </p>
      </div>
    </div>
  );
}
