import React, { useRef, useState } from 'react';
import { SafeAreaView, View, Text, TextInput, TouchableOpacity, Alert, ScrollView } from 'react-native';
import { RTCPeerConnection, mediaDevices, RTCDataChannel } from 'react-native-webrtc';

const styles:any = {
  root: { flex: 1, backgroundColor: '#0b0f14' },
  container: { padding: 16, gap: 12 },
  title: { fontSize: 24, fontWeight: '800', color: 'white' },
  card: { backgroundColor: '#111823', borderRadius: 14, padding: 14, borderWidth: 1, borderColor: '#1b2533' },
  label: { color: '#a7b1bf', marginTop: 4 },
  btn: { backgroundColor: '#ff6600', paddingVertical: 14, borderRadius: 12, alignItems: 'center' },
  btnText: { color: 'white', fontWeight: '700' },
  input: { backgroundColor: '#18202a', color: 'white', padding: 12, borderRadius: 10, marginTop: 6 },
  row: { flexDirection: 'row', gap: 10, alignItems: 'center' },
  pill: { backgroundColor: '#1e2a36', paddingVertical: 8, paddingHorizontal: 12, borderRadius: 999, borderWidth: 1, borderColor: 'transparent' },
  pillActive: { borderColor: '#ff6600' },
  captionItem: { backgroundColor: '#0e1420', borderColor: '#1f2a37', borderWidth: 1, padding: 10, borderRadius: 10, marginBottom: 8 },
  captionLang: { color: '#6fa8ff', fontSize: 12, marginBottom: 4 },
  captionText: { color: 'white', fontSize: 16, lineHeight: 22 },
  hint: { color: '#8aa0b6' }
};

type Cap = { src_lang: string; tgt_lang: string; text: string };

export default function App() {
  const [serverUrl, setServerUrl] = useState('http://YOUR_SERVER_IP:8765/offer');
  const [targetLang, setTargetLang] = useState<'en'|'no'|'pl'>('en');
  const [connected, setConnected] = useState(false);
  const [logPath, setLogPath] = useState<string>('');
  const [caps, setCaps] = useState<Cap[]>([]);

  const pcRef = useRef<RTCPeerConnection | null>(null);
  const chanRef = useRef<RTCDataChannel | null>(null);

  const connect = async () => {
    try {
      const pc = new RTCPeerConnection();
      pcRef.current = pc;

      const stream = await mediaDevices.getUserMedia({ audio: true, video: false });
      stream.getTracks().forEach(t => pc.addTrack(t, stream));

      pc.onconnectionstatechange = () => {
        const st = pc.connectionState;
        if (st === 'connected') setConnected(true);
        if (['disconnected','failed','closed'].includes(st)) setConnected(false);
      };

      pc.ondatachannel = (ev:any) => {
        const chan = ev.channel;
        chanRef.current = chan;
        chan.onmessage = (m:any) => {
          try {
            const msg = JSON.parse(m.data);
            if (msg.type === 'hello' && msg.log_path) {
              setLogPath(msg.log_path);
            } else if (msg.type === 'caption') {
              setCaps(prev => [{ src_lang: msg.src_lang, tgt_lang: msg.tgt_lang, text: msg.text }, ...prev].slice(0, 200));
            }
          } catch {}
        };
      };

      const offer = await pc.createOffer({ offerToReceiveAudio: true });
      await pc.setLocalDescription(offer);
      const payload = { sdp: offer.sdp, target_lang: targetLang };
      const resp = await fetch(serverUrl, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      const answerSdp = await resp.text();
      await pc.setRemoteDescription({ type: 'answer', sdp: answerSdp });
    } catch (e:any) {
      console.error(e);
      Alert.alert('Error', e?.message || 'Failed to connect');
    }
  };

  const disconnect = async () => {
    try {
      pcRef.current?.getSenders().forEach(s => s.track?.stop());
      await pcRef.current?.close();
      pcRef.current = null;
      chanRef.current = null;
      setConnected(false);
    } catch {}
  };

  return (
    <SafeAreaView style={styles.root}>
      <ScrollView contentContainerStyle={{ padding:16, paddingBottom: 40 }}>
        <Text style={styles.title}>Ear Interpreter</Text>

        <View style={styles.card}>
          <Text style={styles.label}>Server Offer URL</Text>
          <TextInput style={styles.input} value={serverUrl} onChangeText={setServerUrl} autoCapitalize="none" />
          <Text style={[styles.label,{marginTop:8}]}>Translate everything to</Text>
          <View style={[styles.row, { marginTop:8 }]}>
            {(['en','no','pl'] as const).map(l => {
              const active = targetLang === l;
              return (
                <TouchableOpacity key={l} style={[styles.pill, active && styles.pillActive]} onPress={()=>setTargetLang(l)}>
                  <Text style={{color:'white', fontWeight:'600'}}>{l.toUpperCase()}</Text>
                </TouchableOpacity>
              )
            })}
          </View>
          <View style={[styles.row, { marginTop:12 }]}>
            <TouchableOpacity style={styles.btn} onPress={connected?disconnect:connect}>
              <Text style={styles.btnText}>{connected ? 'Disconnect' : 'Connect & Start'}</Text>
            </TouchableOpacity>
          </View>
          <Text style={[styles.hint,{marginTop:10}]}>• Audio auto-routes to your Bluetooth earbuds.</Text>
          <Text style={styles.hint}>• Server logs transcripts to a text file.</Text>
          {logPath ? <Text style={[styles.hint,{marginTop:6}]}>Log file: {logPath}</Text> : null}
        </View>

        <View style={[styles.card,{marginTop:14}]}>
          <Text style={{color:'#a7b1bf', marginBottom:8}}>Live captions</Text>
          {caps.length === 0 ? (
            <Text style={styles.hint}>No captions yet. Start speaking near the mic.</Text>
          ) : (
            caps.map((c, idx) => (
              <View key={idx} style={styles.captionItem}>
                <Text style={styles.captionLang}>{c.src_lang.toUpperCase()} → {c.tgt_lang.toUpperCase()}</Text>
                <Text style={styles.captionText}>{c.text}</Text>
              </View>
            ))
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}
