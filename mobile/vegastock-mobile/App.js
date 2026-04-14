import React, { useState } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, Button, FlatList, TextInput, Alert } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';

export default function App() {
  const [permission, requestPermission] = useCameraPermissions();
  
  // ==========================================
  // ESTADOS DE AUTENTICAÇÃO (A FECHADURA)
  // ==========================================
  const [etapaAuth, setEtapaAuth] = useState('INICIO'); // INICIO, ESCOLHA, PIN, SENHA, LOGADO
  const [pinDigitado, setPinDigitado] = useState('');
  const [loginUsuario, setLoginUsuario] = useState('');
  const [senhaUsuario, setSenhaUsuario] = useState('');
  
  const [operadorLogado, setOperadorLogado] = useState('');
  const [clienteIdContexto, setClienteIdContexto] = useState(1); // Fixo em 1 para o PIN (Até termos o QR Code)

  // ==========================================
  // ESTADOS DO ESTOQUE (Mantidos do seu original)
  // ==========================================
  const [custo, setCusto] = useState('');
  const [motivos, setMotivos] = useState([]);
  const [motivoEscolhido, setMotivoEscolhido] = useState(null);
  const [scanned, setScanned] = useState(false);
  const [modo, setModo] = useState(null); 
  const [codigoNovo, setCodigoNovo] = useState(null);
  const [produtoReconhecido, setProdutoReconhecido] = useState(null);
  const [quantidade, setQuantidade] = useState('');
  const [produtosCatalogo, setProdutosCatalogo] = useState([]);

  const API_URL = "https://vegastock.onrender.com";

  if (!permission) return <View />;
  if (!permission.granted) {
    return (
      <View style={styles.container}>
        <Text style={{ textAlign: 'center', marginBottom: 20, fontSize: 18 }}>Precisamos da sua permissão para usar a câmera.</Text>
        <Button onPress={requestPermission} title="Conceder Permissão" color="#FFD700" />
      </View>
    );
  }

  // --- FUNÇÕES DE LOGIN ---
  const handleLoginPin = async () => {
    if(pinDigitado.length !== 4) { Alert.alert("Erro", "O PIN deve ter exatos 4 dígitos."); return; }
    try {
      let res = await fetch(`${API_URL}/validar_pin`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cliente_id: clienteIdContexto, pin: pinDigitado })
      });
      if (res.ok) {
        let dados = await res.json();
        setOperadorLogado(dados.nome);
        setEtapaAuth('LOGADO');
      } else {
        Alert.alert("Erro", "PIN incorreto ou não cadastrado.");
      }
    } catch(e) { Alert.alert("Conexão", "Servidor offline."); }
  };

  const handleLoginSenha = async () => {
    if(!loginUsuario || !senhaUsuario) { Alert.alert("Erro", "Preencha login e senha."); return; }
    try {
      let res = await fetch(`${API_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ login: loginUsuario, senha: senhaUsuario })
      });
      if (res.ok) {
        let dados = await res.json();
        setClienteIdContexto(dados.cliente_id);
        setOperadorLogado(dados.login_usuario);
        setEtapaAuth('LOGADO');
      } else {
        Alert.alert("Erro", "Usuário ou senha incorretos.");
      }
    } catch(e) { Alert.alert("Conexão", "Servidor offline."); }
  };

  // --- FUNÇÕES DA CÂMERA E ESTOQUE ---
  const handleBarCodeScanned = async ({ type, data }) => {
    setScanned(true);
    const codigoLimpo = String(data).trim();

    try {
      let resposta = await fetch(`${API_URL}/produto_por_codigo/${clienteIdContexto}/${codigoLimpo}`);
      if (resposta.status === 200) {
        let produto = await resposta.json();
        setProdutoReconhecido(produto);
      } else if (resposta.status === 404) {
        setCodigoNovo(codigoLimpo); 
        try {
          let resProdutos = await fetch(`${API_URL}/produtos_mobile/${clienteIdContexto}`);
          if (resProdutos.ok) setProdutosCatalogo(await resProdutos.json());
        } catch (e) { Alert.alert("Erro", "Sem conexão para baixar catálogo."); }
      }
    } catch (erro) { Alert.alert("Erro", "Falha de conexão com a API."); }
  };

  const realizarBatismo = async (produto_id) => {
    try {
      const res = await fetch(`${API_URL}/vincular_codigo`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ produto_id: produto_id, codigo_barras: codigoNovo, cliente_id: clienteIdContexto })
      });
      if (res.ok) {
        Alert.alert("Sucesso", "Código vinculado! O sistema já aprendeu.");
        const produtoEscolhido = produtosCatalogo.find(p => p.id === produto_id);
        setCodigoNovo(null);
        setProdutoReconhecido(produtoEscolhido);
      }
    } catch (error) { Alert.alert("Erro", "Sem conexão."); }
  };

  const confirmarMovimentacao = async () => {
    let qtdFormatada = quantidade ? quantidade.replace(',', '.') : '0';
    let custoFormatado = custo ? custo.replace(',', '.') : '0';
    let numQtd = parseFloat(qtdFormatada);
    let numCusto = parseFloat(custoFormatado);

    if (!quantidade || isNaN(numQtd) || numQtd <= 0) { Alert.alert("Erro", "Digite uma quantidade válida!"); return; }
    if (modo === 'Entrada' && (!custo || isNaN(numCusto))) { Alert.alert("Erro", "Digite o custo total!"); return; }
    if (modo === 'Saida' && !motivoEscolhido) { Alert.alert("Erro", "Selecione um motivo para a saída!"); return; }

    try {
      const res = await fetch(`${API_URL}/movimentar_mobile`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          cliente_id: clienteIdContexto,
          produto_id: produtoReconhecido.id,
          tipo_movimento: modo,
          quantidade: numQtd,
          custo_unitario: modo === 'Entrada' ? numCusto : null,
          motivo_baixa_id: modo === 'Saida' ? motivoEscolhido : null,
          operador_nome: operadorLogado // O nome do cara que fez o login!
        })
      });

      if (res.ok) {
        Alert.alert("Sucesso", "Movimentação registrada!");
        setProdutoReconhecido(null); setQuantidade(''); setCusto(''); setMotivoEscolhido(null); setScanned(false); setModo(null);
      }
    } catch (error) { Alert.alert("Erro", "Sem conexão com a API."); }
  };

  // ==========================================
  // RENDERIZAÇÃO DAS TELAS DE LOGIN
  // ==========================================
  
  if (etapaAuth === 'INICIO') {
    return (
      <View style={styles.containerLogin}>
        <Text style={styles.tituloLogin}>VegaStock</Text>
        <Text style={styles.subtituloLogin}>Controle de Estoque</Text>
        <TouchableOpacity style={styles.btnLoginGeral} onPress={() => setEtapaAuth('ESCOLHA')}>
          <Text style={styles.btnText}>FAZER LOGIN</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (etapaAuth === 'ESCOLHA') {
    return (
      <View style={styles.containerLogin}>
        <Text style={styles.tituloSecundario}>Como deseja entrar?</Text>
        <TouchableOpacity style={styles.btnEscolha} onPress={() => setEtapaAuth('PIN')}>
          <Text style={styles.btnTextEscuro}>🔑 Usar PIN Rápido</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.btnEscolha} onPress={() => setEtapaAuth('SENHA')}>
          <Text style={styles.btnTextEscuro}>👤 Usar Usuário e Senha</Text>
        </TouchableOpacity>
        <TouchableOpacity style={{marginTop: 20}} onPress={() => setEtapaAuth('INICIO')}>
          <Text style={{color: '#999'}}>Voltar</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (etapaAuth === 'PIN') {
    return (
      <View style={styles.containerLogin}>
        <Text style={styles.tituloSecundario}>Digite seu PIN</Text>
        <TextInput
          style={styles.inputAuth}
          placeholder="****"
          placeholderTextColor="#999"
          keyboardType="numeric"
          secureTextEntry
          maxLength={4}
          value={pinDigitado}
          onChangeText={setPinDigitado}
        />
        <TouchableOpacity style={styles.btnConfirmarAuth} onPress={handleLoginPin}>
          <Text style={styles.btnText}>ENTRAR</Text>
        </TouchableOpacity>
        <TouchableOpacity style={{marginTop: 20}} onPress={() => setEtapaAuth('ESCOLHA')}>
          <Text style={{color: '#999'}}>Voltar</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (etapaAuth === 'SENHA') {
    return (
      <View style={styles.containerLogin}>
        <Text style={styles.tituloSecundario}>Acesso Restrito</Text>
        <TextInput
          style={styles.inputAuth}
          placeholder="Usuário"
          placeholderTextColor="#999"
          value={loginUsuario}
          onChangeText={setLoginUsuario}
        />
        <TextInput
          style={styles.inputAuth}
          placeholder="Senha"
          placeholderTextColor="#999"
          secureTextEntry
          value={senhaUsuario}
          onChangeText={setSenhaUsuario}
        />
        <TouchableOpacity style={styles.btnConfirmarAuth} onPress={handleLoginSenha}>
          <Text style={styles.btnText}>ENTRAR</Text>
        </TouchableOpacity>
        <TouchableOpacity style={{marginTop: 20}} onPress={() => setEtapaAuth('ESCOLHA')}>
          <Text style={{color: '#999'}}>Voltar</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // ==========================================
  // RENDERIZAÇÃO DAS TELAS DO ESTOQUE (LOGADO)
  // ==========================================

  // TELA 4: Digitar valores
  if (produtoReconhecido) {
    return (
      <View style={styles.container}>
        <Text style={[styles.titulo, { color: modo === 'Entrada' ? '#4CAF50' : '#F44336', fontSize: 30 }]}>
          {modo.toUpperCase()}
        </Text>
        <Text style={{fontSize: 20, fontWeight: 'bold', marginVertical: 10, textAlign: 'center'}}>{produtoReconhecido.nome}</Text>
        
        <TextInput
          style={styles.inputEstoque}
          keyboardType="numeric"
          placeholder={`Quantidade (${produtoReconhecido.unidade_medida})`}
          value={quantidade}
          onChangeText={setQuantidade}
        />

        {modo === 'Entrada' && (
          <TextInput
            style={styles.inputEstoque}
            keyboardType="numeric"
            placeholder="Custo (R$)"
            value={custo}
            onChangeText={setCusto}
          />
        )}

        {modo === 'Saida' && (
          <View style={{width: '90%', height: 180, marginBottom: 15}}>
            <Text style={{textAlign: 'center', fontWeight: 'bold', marginBottom: 5}}>Motivo da Saída:</Text>
            <FlatList
              data={motivos}
              keyExtractor={(item) => item.id.toString()}
              renderItem={({ item }) => (
                <TouchableOpacity 
                  style={{
                    backgroundColor: motivoEscolhido === item.id ? '#F44336' : '#ddd',
                    padding: 12, marginVertical: 4, borderRadius: 5
                  }}
                  onPress={() => setMotivoEscolhido(item.id)}
                >
                  <Text style={{color: motivoEscolhido === item.id ? '#fff' : '#000', textAlign: 'center', fontWeight: 'bold'}}>
                    {item.descricao}
                  </Text>
                </TouchableOpacity>
              )}
            />
          </View>
        )}

        <View style={{width: '90%'}}>
          <Button title="CONFIRMAR" color={modo === 'Entrada' ? '#4CAF50' : '#F44336'} onPress={confirmarMovimentacao} />
          <View style={{marginTop: 15}}>
            <Button title="Cancelar" color="#333" onPress={() => { 
              setProdutoReconhecido(null); setQuantidade(''); setCusto(''); setMotivoEscolhido(null); setScanned(false); 
            }} />
          </View>
        </View>
      </View>
    );
  }

  // TELA 3: Batismo
  if (codigoNovo) {
    return (
      <View style={styles.container}>
        <Text style={[styles.titulo, {fontSize: 30, color: '#FFD700'}]}>Código Novo!</Text>
        <Text style={{fontSize: 16, marginBottom: 20, textAlign: 'center'}}>A qual produto o código {codigoNovo} pertence?</Text>
        
        <FlatList
          data={produtosCatalogo}
          keyExtractor={(item) => item.id.toString()}
          style={{ width: '100%', marginBottom: 20 }}
          renderItem={({ item }) => (
            <TouchableOpacity 
              style={{backgroundColor: '#e0e0e0', padding: 15, marginVertical: 5, borderRadius: 8}}
              onPress={() => realizarBatismo(item.id)}
            >
              <Text style={{fontSize: 16, fontWeight: 'bold'}}>{item.nome}</Text>
            </TouchableOpacity>
          )}
        />
        
        <Button title="Cancelar e Voltar" color="#F44336" onPress={() => { setCodigoNovo(null); setScanned(false); }} />
      </View>
    );
  }

  // TELA 2: Câmera
  if (modo) {
    return (
      <View style={styles.containerCamera}>
        <CameraView
          style={StyleSheet.absoluteFillObject}
          facing="back"
          onBarcodeScanned={scanned ? undefined : handleBarCodeScanned}
          barcodeScannerSettings={{ barcodeTypes: ["ean13", "ean8", "qr", "upc_a"] }}
        />
        <View style={styles.overlay}>
          <Text style={styles.textoScan}>Lendo código para {modo}...</Text>
          {scanned && <Button title={'Tocar para ler novamente'} onPress={() => setScanned(false)} />}
          
          <TouchableOpacity style={styles.btnVoltar} onPress={() => setModo(null)}>
            <Text style={styles.btnTextPequeno}>Cancelar e Voltar</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  // TELA 1: Menu Principal (Logado)
  return (
    <View style={styles.container}>
      <Text style={styles.titulo}>VegaStock</Text>
      <Text style={styles.subtitulo}>Operador: {operadorLogado}</Text>

      <TouchableOpacity style={[styles.botao, styles.btnEntrada]} onPress={() => { setModo('Entrada'); setScanned(false); }}>
        <Text style={styles.btnText}>⬇️ ENTRADA</Text>
      </TouchableOpacity>

      <TouchableOpacity style={[styles.botao, styles.btnSaida]} onPress={async () => { 
          setModo('Saida'); setScanned(false); 
          try {
            let res = await fetch(`${API_URL}/motivos_mobile/${clienteIdContexto}`);
            setMotivos(await res.json());
          } catch(e) {}
        }}>
        <Text style={styles.btnText}>⬆️ SAÍDA</Text>
      </TouchableOpacity>

      <TouchableOpacity style={{marginTop: 30}} onPress={() => setEtapaAuth('INICIO')}>
        <Text style={{color: '#999', textDecorationLine: 'underline'}}>Sair (Logoff)</Text>
      </TouchableOpacity>
    </View>
  );
}

// ==========================================
// CSS DO APLICATIVO
// ==========================================
const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#f5f5f5', padding: 20 },
  containerCamera: { flex: 1, justifyContent: 'center' },
  
  // Estilos do Login
  containerLogin: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#1a1a1f', padding: 20 },
  tituloLogin: { fontSize: 45, fontWeight: 'bold', color: '#FFD700', marginBottom: 5 },
  subtituloLogin: { fontSize: 18, color: '#aaa', marginBottom: 50 },
  tituloSecundario: { fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 30 },
  
  btnLoginGeral: { width: '80%', padding: 20, backgroundColor: '#009EE3', borderRadius: 10, alignItems: 'center' },
  btnEscolha: { width: '80%', padding: 20, backgroundColor: '#fff', borderRadius: 10, alignItems: 'center', marginBottom: 15 },
  btnConfirmarAuth: { width: '80%', padding: 15, backgroundColor: '#FFD700', borderRadius: 10, alignItems: 'center', marginTop: 10 },
  
  btnTextEscuro: { color: '#000', fontSize: 18, fontWeight: 'bold' },
  inputAuth: { width: '80%', backgroundColor: '#2b2b36', color: '#fff', fontSize: 18, padding: 15, borderRadius: 10, marginBottom: 15, borderWidth: 1, borderColor: '#444', textAlign: 'center' },
  
  // Estilos do Estoque
  titulo: { fontSize: 35, fontWeight: 'bold', color: '#333', marginBottom: 5 },
  subtitulo: { fontSize: 16, color: '#777', marginBottom: 40, fontWeight: 'bold' },
  
  botao: { width: '100%', padding: 30, borderRadius: 15, alignItems: 'center', marginBottom: 20, elevation: 5 },
  btnEntrada: { backgroundColor: '#4CAF50' },
  btnSaida: { backgroundColor: '#F44336' },
  btnText: { color: '#fff', fontSize: 22, fontWeight: 'bold' },
  
  inputEstoque: { borderWidth: 2, borderColor: '#ccc', width: '90%', fontSize: 24, padding: 15, textAlign: 'center', borderRadius: 10, marginBottom: 15, backgroundColor: '#fff' },
  
  overlay: { flex: 1, backgroundColor: 'transparent', justifyContent: 'flex-end', padding: 20, marginBottom: 30 },
  textoScan: { backgroundColor: 'rgba(0,0,0,0.8)', color: 'white', padding: 15, textAlign: 'center', fontSize: 20, fontWeight: 'bold', borderRadius: 8, marginBottom: 20 },
  btnVoltar: { backgroundColor: '#333', padding: 20, borderRadius: 10, alignItems: 'center', marginTop: 10 },
  btnTextPequeno: { color: '#fff', fontSize: 18, fontWeight: 'bold' }
});