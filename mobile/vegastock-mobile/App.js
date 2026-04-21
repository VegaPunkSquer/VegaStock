import React, { useState } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, TextInput, Alert, FlatList, Image } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';

export default function App() {
  const [permission, requestPermission] = useCameraPermissions();
  
  // ==========================================
  // ESTADOS DE AUTENTICAÇÃO (O SEU FLUXO ORIGINAL)
  // ==========================================
  const [etapaAuth, setEtapaAuth] = useState('INICIO'); // INICIO, PIN, SENHA, LOGADO
  
  // Dados do Restaurante/Login
  const [clienteIdContexto, setClienteIdContexto] = useState(1); // Fixo em 1 pro PIN até você fazer o QR Code
  const [nomeFantasia, setNomeFantasia] = useState('VegaStock');
  const [logoRestaurante, setLogoRestaurante] = useState(null);
  const [operadorLogado, setOperadorLogado] = useState('');
  
  // Inputs
  const [loginUsuario, setLoginUsuario] = useState('');
  const [senhaUsuario, setSenhaUsuario] = useState('');
  const [pinDigitado, setPinDigitado] = useState('');

  // ==========================================
  // ESTADOS DO ESTOQUE
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
      <View style={styles.containerEscuro}>
        <Text style={{ textAlign: 'center', marginBottom: 20, fontSize: 18, color: '#fff' }}>Precisamos da câmera para ler os códigos.</Text>
        <TouchableOpacity style={styles.btnConfirmarAuth} onPress={requestPermission}>
          <Text style={styles.btnTextEscuro}>Conceder Permissão</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // --- LOGIN VIA SENHA (EQUIPE PRO) ---
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
        setNomeFantasia(dados.nome_fantasia || "Restaurante");
        setLogoRestaurante(dados.logo_url);
        setOperadorLogado(loginUsuario.toUpperCase()); // Carimba o nome do cara
        
        setLoginUsuario(''); setSenhaUsuario('');
        setEtapaAuth('LOGADO');
      } else {
        Alert.alert("Acesso Negado", "Usuário ou senha incorretos.");
      }
    } catch(e) { Alert.alert("Conexão", "Servidor offline."); }
  };

  // --- LOGIN VIA PIN (OPERADOR BÁSICO) ---
  const handleLoginPin = async () => {
    if(pinDigitado.length !== 4) { Alert.alert("Erro", "O PIN deve ter 4 dígitos."); return; }
    try {
      let res = await fetch(`${API_URL}/validar_pin`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cliente_id: clienteIdContexto, pin: pinDigitado })
      });
      if (res.ok) {
        let dados = await res.json();
        setOperadorLogado(dados.nome);
        setPinDigitado('');
        setEtapaAuth('LOGADO');
      } else {
        Alert.alert("Erro", "PIN incorreto.");
        setPinDigitado('');
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
        setProdutoReconhecido(await resposta.json());
      } else if (resposta.status === 404) {
        setCodigoNovo(codigoLimpo); 
        try {
          let resProdutos = await fetch(`${API_URL}/produtos_mobile/${clienteIdContexto}`);
          if (resProdutos.ok) setProdutosCatalogo(await resProdutos.json());
        } catch (e) {}
      }
    } catch (erro) { Alert.alert("Erro", "Falha na conexão."); }
  };

  const realizarBatismo = async (produto_id) => {
    try {
      const res = await fetch(`${API_URL}/vincular_codigo`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ produto_id: produto_id, codigo_barras: codigoNovo, cliente_id: clienteIdContexto })
      });
      if (res.ok) {
        Alert.alert("Sucesso", "Código vinculado!");
        const produtoEscolhido = produtosCatalogo.find(p => p.id === produto_id);
        setCodigoNovo(null);
        setProdutoReconhecido(produtoEscolhido);
      }
    } catch (error) {}
  };

  const confirmarMovimentacao = async () => {
    let numQtd = parseFloat(quantidade ? quantidade.replace(',', '.') : '0');
    let numCusto = parseFloat(custo ? custo.replace(',', '.') : '0');

    if (!quantidade || isNaN(numQtd) || numQtd <= 0) { Alert.alert("Erro", "Quantidade inválida!"); return; }
    if (modo === 'Entrada' && (!custo || isNaN(numCusto))) { Alert.alert("Erro", "Custo inválido!"); return; }
    if (modo === 'Saida' && !motivoEscolhido) { Alert.alert("Erro", "Selecione o motivo!"); return; }

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
          operador_nome: operadorLogado // AQUI ESTÁ A AUDITORIA QUE FIZEMOS HOJE!
        })
      });

      if (res.ok) {
        Alert.alert("Sucesso", "Movimentação registrada!");
        setProdutoReconhecido(null); setQuantidade(''); setCusto(''); setMotivoEscolhido(null); setScanned(false); setModo(null);
      }
    } catch (error) { Alert.alert("Erro", "Sem conexão."); }
  };

  // ==========================================
  // RENDERIZAÇÃO DAS TELAS
  // ==========================================
  
  // TELA 1: ESCOLHA DE ACESSO
  if (etapaAuth === 'INICIO') {
    return (
      <View style={styles.containerEscuro}>
        <Text style={styles.tituloSecundario}>Bem-vindo ao</Text>
        <Text style={{fontSize: 40, fontWeight: 'bold', color: '#FFD700', marginBottom: 50}}>VegaStock</Text>
        
        <TouchableOpacity style={styles.botaoGigante} onPress={() => setEtapaAuth('SENHA')}>
          <Text style={styles.btnTextEscuro}>Acesso da Equipe</Text>
          <Text style={{color: '#333'}}>Login e Senha</Text>
        </TouchableOpacity>

        <TouchableOpacity style={[styles.botaoGigante, {backgroundColor: '#333', borderColor: '#555', borderWidth: 1}]} onPress={() => setEtapaAuth('PIN')}>
          <Text style={styles.btnText}>Acesso Rápido</Text>
          <Text style={{color: '#aaa'}}>PIN Operacional</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // TELA 2: LOGIN DA EQUIPE (Senha)
  if (etapaAuth === 'SENHA') {
    return (
      <View style={styles.containerEscuro}>
        <Text style={styles.tituloSecundario}>Acesso da Equipe</Text>
        <TextInput style={styles.inputAuth} placeholder="Login" placeholderTextColor="#777" value={loginUsuario} onChangeText={setLoginUsuario} />
        <TextInput style={styles.inputAuth} placeholder="Senha" placeholderTextColor="#777" secureTextEntry value={senhaUsuario} onChangeText={setSenhaUsuario} />
        
        <TouchableOpacity style={styles.btnConfirmarAuth} onPress={handleLoginSenha}>
          <Text style={styles.btnTextEscuro}>ENTRAR</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={{marginTop: 30}} onPress={() => setEtapaAuth('INICIO')}>
          <Text style={{color: '#aaa'}}>Voltar</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // TELA 3: LOGIN RÁPIDO (PIN)
  if (etapaAuth === 'PIN') {
    return (
      <View style={styles.containerEscuro}>
        <Text style={styles.tituloSecundario}>Operador de Turno</Text>
        <Text style={{color: '#fff', fontSize: 18, marginBottom: 15}}>Digite seu PIN de 4 dígitos</Text>
        
        <TextInput style={styles.inputPin} placeholder="****" placeholderTextColor="#777" keyboardType="numeric" secureTextEntry maxLength={4} value={pinDigitado} onChangeText={setPinDigitado} />
        
        <TouchableOpacity style={styles.btnConfirmarAuth} onPress={handleLoginPin}>
          <Text style={styles.btnTextEscuro}>ACESSAR</Text>
        </TouchableOpacity>

        <TouchableOpacity style={{marginTop: 30}} onPress={() => setEtapaAuth('INICIO')}>
          <Text style={{color: '#aaa'}}>Voltar</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // TELA 4: OPERAÇÃO (Logado)
  if (etapaAuth === 'LOGADO') {
    // Inteligência do Avatar Visual
    const ehLinkWeb = logoRestaurante && logoRestaurante.startsWith('http');

    if (produtoReconhecido) {
      // (Mantido igual: Tela de digitar Quantidade e Custo)
      return (
        <View style={styles.containerBranco}>
          <Text style={[styles.tituloMaior, { color: modo === 'Entrada' ? '#4CAF50' : '#F44336' }]}>{modo.toUpperCase()}</Text>
          <Text style={{fontSize: 22, fontWeight: 'bold', marginVertical: 15, textAlign: 'center'}}>{produtoReconhecido.nome}</Text>
          
          <View style={{width: '90%', marginBottom: 5}}>
            <Text style={{fontSize: 16, fontWeight: 'bold', color: '#555', marginBottom: 5}}>Quantidade ({produtoReconhecido.unidade_medida}):</Text>
            <TextInput style={[styles.inputEstoque, {width: '100%'}]} keyboardType="numeric" placeholder="Ex: 10" value={quantidade} onChangeText={setQuantidade} />
          </View>

          {modo === 'Entrada' && (
            <View style={{width: '90%', marginBottom: 5}}>
              <Text style={{fontSize: 16, fontWeight: 'bold', color: '#555', marginBottom: 5}}>Custo Unitário (R$):</Text>
              <TextInput style={[styles.inputEstoque, {width: '100%'}]} keyboardType="numeric" placeholder="Ex: 50.00" value={custo} onChangeText={setCusto} />
            </View>
          )}

          {modo === 'Saida' && (
            <View style={{width: '90%', height: 200, marginBottom: 15}}>
              <Text style={{textAlign: 'center', fontWeight: 'bold', marginBottom: 10, fontSize: 16}}>Motivo da Saída:</Text>
              <FlatList data={motivos} keyExtractor={(item) => item.id.toString()} renderItem={({ item }) => (
                  <TouchableOpacity 
                    style={{ backgroundColor: motivoEscolhido === item.id ? '#F44336' : '#eee', padding: 15, marginVertical: 4, borderRadius: 8, borderWidth: 1, borderColor: '#ddd' }}
                    onPress={() => setMotivoEscolhido(item.id)} >
                    <Text style={{color: motivoEscolhido === item.id ? '#fff' : '#333', textAlign: 'center', fontWeight: 'bold', fontSize: 16}}>{item.descricao}</Text>
                  </TouchableOpacity>
                )} />
            </View>
          )}

          <View style={{width: '90%', marginTop: 20}}>
            <TouchableOpacity style={[styles.btnConfirmarAuth, {backgroundColor: modo === 'Entrada' ? '#4CAF50' : '#F44336'}]} onPress={confirmarMovimentacao}>
              <Text style={styles.btnText}>CONFIRMAR</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.btnConfirmarAuth, {backgroundColor: '#333', marginTop: 10}]} onPress={() => { 
                setProdutoReconhecido(null); setQuantidade(''); setCusto(''); setMotivoEscolhido(null); setScanned(false); 
              }}>
              <Text style={styles.btnText}>CANCELAR</Text>
            </TouchableOpacity>
          </View>
        </View>
      );
    }

    if (codigoNovo) {
      // (Mantido igual: Tela de Batismo)
      return (
        <View style={styles.containerBranco}>
          <Text style={{fontSize: 28, fontWeight: 'bold', color: '#FF9800', marginBottom: 10}}>Código Novo!</Text>
          <Text style={{fontSize: 18, marginBottom: 20, textAlign: 'center', paddingHorizontal: 20}}>A qual produto o código {codigoNovo} pertence?</Text>
          <FlatList data={produtosCatalogo} keyExtractor={(item) => item.id.toString()} style={{ width: '90%', marginBottom: 20 }} renderItem={({ item }) => (
              <TouchableOpacity style={{backgroundColor: '#fff', padding: 18, marginVertical: 5, borderRadius: 8, borderWidth: 1, borderColor: '#ddd'}} onPress={() => realizarBatismo(item.id)}>
                <Text style={{fontSize: 18, fontWeight: 'bold', color: '#333'}}>{item.nome}</Text>
              </TouchableOpacity>
            )} />
          <TouchableOpacity style={[styles.btnConfirmarAuth, {backgroundColor: '#F44336', width: '90%'}]} onPress={() => { setCodigoNovo(null); setScanned(false); }}>
            <Text style={styles.btnText}>CANCELAR BATISMO</Text>
          </TouchableOpacity>
        </View>
      );
    }

    if (modo) {
      // (Mantido igual: Tela da Câmera)
      return (
        <View style={styles.containerCamera}>
          <CameraView style={StyleSheet.absoluteFillObject} facing="back" onBarcodeScanned={scanned ? undefined : handleBarCodeScanned} barcodeScannerSettings={{ barcodeTypes: ["ean13", "ean8", "qr", "upc_a"] }} />
          <View style={styles.overlay}>
            <Text style={styles.textoScan}>Lendo código para {modo}...</Text>
            {scanned && (
              <TouchableOpacity style={[styles.btnConfirmarAuth, {backgroundColor: '#FFD700', marginBottom: 10}]} onPress={() => setScanned(false)}>
                 <Text style={styles.btnTextEscuro}>TOCAR PARA LER NOVAMENTE</Text>
              </TouchableOpacity>
            )}
            <TouchableOpacity style={[styles.btnConfirmarAuth, {backgroundColor: '#F44336'}]} onPress={() => setModo(null)}>
              <Text style={styles.btnText}>VOLTAR</Text>
            </TouchableOpacity>
          </View>
        </View>
      );
    }

    // MENU PRINCIPAL DO ESTOQUE
    return (
      <View style={styles.containerBranco}>
        {/* AVATAR/LOGO INTELIGENTE */}
        {ehLinkWeb ? (
          <Image source={{ uri: logoRestaurante }} style={styles.logoImage} />
        ) : (
          <View style={styles.logoFallback}>
            <Text style={styles.logoFallbackText}>{nomeFantasia.charAt(0).toUpperCase()}</Text>
          </View>
        )}
        
        <Text style={styles.tituloMenu}>{nomeFantasia}</Text>
        <Text style={{fontSize: 16, color: '#666', marginBottom: 40}}>Operador: <Text style={{fontWeight: 'bold', color: '#333'}}>{operadorLogado}</Text></Text>

        <TouchableOpacity style={[styles.botaoAcao, {backgroundColor: '#4CAF50'}]} onPress={() => { setModo('Entrada'); setScanned(false); }}>
          <Text style={styles.btnText}>⬇️ REGISTRAR ENTRADA</Text>
        </TouchableOpacity>

        <TouchableOpacity style={[styles.botaoAcao, {backgroundColor: '#F44336'}]} onPress={async () => { 
            setModo('Saida'); setScanned(false); 
            try {
              let res = await fetch(`${API_URL}/motivos_mobile/${clienteIdContexto}`);
              setMotivos(await res.json());
            } catch(e) {}
          }}>
          <Text style={styles.btnText}>⬆️ REGISTRAR SAÍDA</Text>
        </TouchableOpacity>

        <TouchableOpacity style={{marginTop: 50, padding: 15, backgroundColor: '#eee', borderRadius: 8}} onPress={() => {
            setOperadorLogado(''); setEtapaAuth('INICIO'); 
          }}>
          <Text style={{color: '#f44336', fontWeight: 'bold', fontSize: 16}}>🚪 SAIR DA CONTA</Text>
        </TouchableOpacity>
      </View>
    );
  }
}

// ==========================================
// CSS DO APLICATIVO
// ==========================================
const styles = StyleSheet.create({
  containerEscuro: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#1a1a1f', padding: 20 },
  containerBranco: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#f5f5f5', padding: 20 },
  containerCamera: { flex: 1, justifyContent: 'center' },
  
  // Elementos Visuais
  logoImage: { width: 100, height: 100, borderRadius: 50, marginBottom: 10, borderWidth: 2, borderColor: '#ccc' },
  logoFallback: { width: 100, height: 100, borderRadius: 50, backgroundColor: '#333', justifyContent: 'center', alignItems: 'center', marginBottom: 10, borderWidth: 2, borderColor: '#555' },
  logoFallbackText: { fontSize: 45, fontWeight: 'bold', color: '#FFD700' },
  
  tituloSecundario: { fontSize: 24, color: '#fff', marginBottom: 5 },
  tituloMenu: { fontSize: 28, fontWeight: 'bold', color: '#333', marginBottom: 5, textAlign: 'center' },
  tituloMaior: { fontSize: 35, fontWeight: 'bold', marginBottom: 5 },
  
  // Botões e Inputs
  btnConfirmarAuth: { width: '90%', padding: 15, backgroundColor: '#FFD700', borderRadius: 10, alignItems: 'center', marginTop: 15 },
  botaoGigante: { width: '90%', padding: 25, backgroundColor: '#FFD700', borderRadius: 15, alignItems: 'center', marginBottom: 20, elevation: 3 },
  botaoAcao: { width: '90%', padding: 25, borderRadius: 15, alignItems: 'center', marginBottom: 20, elevation: 5 },
  
  btnText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  btnTextEscuro: { color: '#000', fontSize: 20, fontWeight: 'bold' },
  
  inputAuth: { width: '90%', backgroundColor: '#2b2b36', color: '#fff', fontSize: 18, padding: 15, borderRadius: 10, marginBottom: 15, borderWidth: 1, borderColor: '#444', textAlign: 'center' },
  inputPin: { width: '80%', backgroundColor: '#1a1a1f', color: '#FFD700', fontSize: 40, padding: 15, borderRadius: 10, borderWidth: 2, borderColor: '#555', textAlign: 'center', letterSpacing: 15 },
  inputEstoque: { borderWidth: 2, borderColor: '#ccc', width: '90%', fontSize: 24, padding: 15, textAlign: 'center', borderRadius: 10, marginBottom: 15, backgroundColor: '#fff' },
  
  // Câmera
  overlay: { flex: 1, backgroundColor: 'transparent', justifyContent: 'flex-end', padding: 20, marginBottom: 30 },
  textoScan: { backgroundColor: 'rgba(0,0,0,0.8)', color: 'white', padding: 15, textAlign: 'center', fontSize: 20, fontWeight: 'bold', borderRadius: 8, marginBottom: 20 },
});