import React, { useState } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, TextInput, Alert, FlatList, Image, ActivityIndicator } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';

export default function App() {
  const [permission, requestPermission] = useCameraPermissions();
  
  // ==========================================
  // ESTADOS DE AUTENTICAÇÃO (O SEU FLUXO ORIGINAL)
  // ==========================================
  const [etapaAuth, setEtapaAuth] = useState('INICIO'); // INICIO, PIN, SENHA, LOGADO
  const [carregando, setCarregando] = useState(false);
  
  // Dados do Restaurante/Login
  const [clienteIdContexto, setClienteIdContexto] = useState(1); // Fixo em 1 pro PIN até você fazer o QR Code
  const [nomeFantasia, setNomeFantasia] = useState('VegaStock');
  const [logoRestaurante, setLogoRestaurante] = useState(null);
  const [operadorLogado, setOperadorLogado] = useState('');
  
  // Inputs
  const [loginUsuario, setLoginUsuario] = useState('');
  const [senhaUsuario, setSenhaUsuario] = useState('');
  const [pinDigitado, setPinDigitado] = useState('');

  // Controle de Pareamento e Olhinhos (Novos e sem duplicidade)
  const [empresaPareada, setEmpresaPareada] = useState(false); 
  const [ocultarSenha, setOcultarSenha] = useState(true);
  const [ocultarPin, setOcultarPin] = useState(true);

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

  const API_URL = "https://vegap-vega-stock.hf.space";

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
    setCarregando(true);
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
    finally { setCarregando(false); }
  };

  // --- LOGIN VIA PIN (OPERADOR BÁSICO) ---
  const handleLoginPin = async () => {
    if(pinDigitado.length !== 4) { Alert.alert("Erro", "O PIN deve ter 4 dígitos."); return; }
    setCarregando(true);
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
    finally { setCarregando(false); }
  };

  // --- FUNÇÕES DA CÂMERA E ESTOQUE ---
  const handleBarCodeScanned = async ({ type, data }) => {
    setScanned(true);
    const codigoLimpo = String(data).trim();

    // ========================================================
    // INTERCEPTADOR DE PAREAMENTO: Se não tiver pareado, o bip é do monitor!
    // ========================================================
    if (!empresaPareada) {
      const idCapturado = parseInt(codigoLimpo, 10);
      if (!isNaN(idCapturado)) {
        setClienteIdContexto(idCapturado);
        setEmpresaPareada(true);
        setEtapaAuth('LOGIN_UNIFICADO'); // Joga para a nova tela de login único que vamos criar
        Alert.alert("Sucesso", "Celular vinculado ao estabelecimento com sucesso!");
      } else {
        Alert.alert("Erro", "QR Code de pareamento inválido.");
      }
      return; // Para a execução aqui para não tentar buscar o ID como produto
    }

    // Fluxo original de bipes de produtos mantido intacto
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
  
  // TELA 1: ESCOLHA DE ACESSO (UNIFICADA COM PAREAMENTO)
  if (etapaAuth === 'INICIO') {
    // Se o celular já guardou o pareamento do monitor, pula o bloqueio e abre direto o Login Unificado
    if (empresaPareada) {
      setEtapaAuth('LOGIN_UNIFICADO');
    }

    return (
      <View style={styles.containerEscuro}>
        <Text style={styles.tituloSecundario}>Bem-vindo ao</Text>
        <Text style={{fontSize: 40, fontWeight: 'bold', color: '#FFD700', marginBottom: 20}}>VegaStock</Text>
        
        <Text style={{color: '#aaa', fontSize: 15, textAlign: 'center', marginHorizontal: 25, marginBottom: 40, lineHeight: 22}}>
          Para iniciar, vincule este aplicativo ao painel administrativo do seu computador.
        </Text>

        <TouchableOpacity 
          style={[styles.botaoGigante, {backgroundColor: '#2196F3', borderColor: '#2196F3', borderWidth: 0}]} 
          onPress={() => { setScanned(false); setModoCamera(true); }}
        >
          <Text style={[styles.btnTextEscuro, {color: '#fff', fontSize: 18}]}>📷 Vincular Estabelecimento</Text>
          <Text style={{color: '#e0e0e0', fontSize: 13, marginTop: 4}}>Escanear QR Code no Monitor</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // ========================================================
  // TELA 2: PORTA DE LOGIN UNIFICADA (SENHA OU PIN NA MESMA CAIXA)
  // ========================================================
  if (etapaAuth === 'LOGIN_UNIFICADO') {
    // Função mestre que decide se valida como PIN de 4 números ou conta de Equipe
    const executarLoginInteligente = () => {
      const credencial = senhaUsuario.trim();
      
      if (!loginUsuario.trim() || !credencial) {
        Alert.alert("Aviso", "Preencha o usuário e a senha/PIN.");
        return;
      }

      // Se tiver exatamente 4 dígitos e for apenas números, roda a validação do PIN Operacional
      if (credencial.length === 4 && /^\d+$/.test(credencial)) {
        // Copia a credencial para o estado do PIN que o seu validador antigo usa
        setPinDigitado(credencial);
        validarPinOperador();
      } else {
        // Se for texto ou maior, roda o validador padrão de equipes
        fazerLoginEquipe();
      }
    };

    return (
      <View style={styles.containerEscuro}>
        <Text style={styles.tituloSecundario}>Acesso ao Estoque</Text>
        <Text style={{color: '#aaa', fontSize: 14, marginBottom: 25, textAlign: 'center', marginHorizontal: 20}}>
          Digite seu usuário e sua senha de acesso ou seu PIN operacional de 4 números.
        </Text>

        <TextInput 
          style={styles.inputAuth} 
          placeholder="Usuário / Operador" 
          placeholderTextColor="#777" 
          value={loginUsuario} 
          onChangeText={setLoginUsuario} 
          autoCapitalize="none"
        />
        
        {/* Bloco horizontal único do olhinho inteligente */}
        <View style={{ width: '90%', flexDirection: 'row', alignItems: 'center', backgroundColor: '#2b2b36', borderRadius: 10, marginBottom: 25, borderWidth: 1, borderColor: '#444' }}>
          <TextInput 
            style={{ flex: 1, color: '#fff', fontSize: 18, padding: 15, textAlign: 'center' }} 
            placeholder="Senha ou PIN" 
            placeholderTextColor="#777" 
            secureTextEntry={ocultarSenha} 
            value={senhaUsuario} 
            onChangeText={setSenhaUsuario} 
          />
          <TouchableOpacity style={{ padding: 15 }} onPress={() => setOcultarSenha(!ocultarSenha)}>
            <Text style={{ fontSize: 20 }}>{ocultarSenha ? '👁️' : '🔒'}</Text>
          </TouchableOpacity>
        </View>
        
        <TouchableOpacity style={styles.btnConfirmarAuth} onPress={executarLoginInteligente}>
          <Text style={styles.btnTextEscuro}>Conectar</Text>
        </TouchableOpacity>

        <TouchableOpacity style={{marginTop: 25}} onPress={() => { setEmpresaPareada(false); setEtapaAuth('INICIO'); }}>
          <Text style={{color: '#f44336', fontWeight: 'bold'}}>🔄 Desvincular Empresa</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // TELA 3: OPERAÇÃO (Logado)
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

        {/* Adicionado largura fixa de 90% idêntica aos outros botões e centralização de texto flexível */}
        <TouchableOpacity style={{width: '90%', marginTop: 40, padding: 15, backgroundColor: '#eee', borderRadius: 12, alignItems: 'center', justifyContent: 'center'}} onPress={() => {
            setOperadorLogado(''); setEtapaAuth('INICIO'); 
          }}>
          <Text style={{color: '#f44336', fontWeight: 'bold', fontSize: 16, textAlign: 'center'}}>
            🚪 SAIR DA CONTA
          </Text>
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