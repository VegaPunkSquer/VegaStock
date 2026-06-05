import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, TextInput, Alert, FlatList, Image, ActivityIndicator, Vibration } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Audio } from 'expo-av';

export default function App() {
  const [permission, requestPermission] = useCameraPermissions();

  // MÁGICA DA MEMÓRIA: Carrega o restaurante salvo assim que o app abre
  useEffect(() => {
    const carregarPareamento = async () => {
      try {
        const idSalvo = await AsyncStorage.getItem('vegastock_cliente_id');
        if (idSalvo !== null) {
          setClienteIdContexto(parseInt(idSalvo, 10));
          setEmpresaPareada(true);
          setEtapaAuth('LOGIN_UNIFICADO');
        }
      } catch (e) {}
    };
    carregarPareamento();
  }, []);
  
  // Controle da Câmera vs Busca Manual
  const [modoCamera, setModoCamera] = useState(true); 
  const [textoBuscaManual, setTextoBuscaManual] = useState('');
  
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
  // Controle do Novo Cadastro pelo Celular
  const [cadastrandoNovo, setCadastrandoNovo] = useState(false);
  const [nomeNovoProd, setNomeNovoProd] = useState('');
  const [unidadeNovoProd, setUnidadeNovoProd] = useState('');

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
  const fazerLoginAPI_Senha = async (loginStr, senhaStr) => {
    setCarregando(true);
    try {
      let res = await fetch(`${API_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ login: loginStr, senha: senhaStr })
      });
      if (res.ok) {
        let dados = await res.json();
        setClienteIdContexto(dados.cliente_id);
        setNomeFantasia(dados.nome_fantasia || "Restaurante");
        setLogoRestaurante(dados.logo_url);
        setOperadorLogado(loginStr.toUpperCase());
        setLoginUsuario(''); setSenhaUsuario('');
        setEtapaAuth('LOGADO');
      } else {
        Alert.alert("Acesso Negado", "Usuário ou senha incorretos.");
      }
    } catch(e) { Alert.alert("Conexão", "Servidor offline."); }
    finally { setCarregando(false); }
  };

  // --- LOGIN VIA PIN (OPERADOR BÁSICO) ---
  const fazerLoginAPI_PIN = async (pinStr) => {
    setCarregando(true);
    try {
      let res = await fetch(`${API_URL}/validar_pin`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cliente_id: clienteIdContexto, pin: pinStr })
      });
      if (res.ok) {
        let dados = await res.json();
        setOperadorLogado(dados.nome);
        setLoginUsuario(''); setSenhaUsuario('');
        setEtapaAuth('LOGADO');
      } else {
        Alert.alert("Erro", "PIN incorreto.");
      }
    } catch(e) { Alert.alert("Conexão", "Servidor offline."); }
    finally { setCarregando(false); }
  };

  // Função para tocar o Bip
  const tocarBip = async () => {
    try {
      const { sound } = await Audio.Sound.createAsync(
        require('./assets/beep.mp3') // Certifique-se de que este arquivo existe!
      );
      await sound.playAsync();
      
      // Limpa a memória depois de tocar para o app não explodir de memória
      sound.setOnPlaybackStatusUpdate((status) => {
        if (status.didJustFinish) {
          sound.unloadAsync();
        }
      });
    } catch (error) {
      console.log("Erro ao tocar o bip", error);
    }
  };

  // --- FUNÇÕES DA CÂMERA E ESTOQUE ---
  const handleBarCodeScanned = async ({ type, data }) => {
    setScanned(true);
    const codigoLimpo = String(data).trim();

    // Toca o som e vibra o celular por 100 milissegundos
    Vibration.vibrate(100);
    tocarBip();

    // ========================================================
    // INTERCEPTADOR DE PAREAMENTO: Se não tiver pareado, o bip é do monitor!
    // ========================================================
    if (!empresaPareada) {
      const idCapturado = parseInt(codigoLimpo, 10);
      if (!isNaN(idCapturado)) {
        setClienteIdContexto(idCapturado);
        setEmpresaPareada(true);
        AsyncStorage.setItem('vegastock_cliente_id', idCapturado.toString()); // <-- GRAVA NO CELULAR!
        setEtapaAuth('LOGIN_UNIFICADO'); 
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

  const cadastrarProdutoPeloCelular = async () => {
    if (!nomeNovoProd || !unidadeNovoProd) {
      Alert.alert("Aviso", "Preencha o nome e a unidade (ex: un, kg).");
      return;
    }
    
    try {
      const res = await fetch(`${API_URL}/produtos`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          cliente_id: clienteIdContexto,
          nome: nomeNovoProd,
          categoria_id: null,
          unidade_medida: unidadeNovoProd.toLowerCase(),
          estoque_minimo: 0,
          codigo_barras: codigoNovo // Já nasce vinculado!
        })
      });

      if (res.ok) {
        const resposta = await res.json();
        Alert.alert("Sucesso", "Produto cadastrado e vinculado!");
        
        // Joga o funcionário direto pra tela de dar a entrada no produto novinho
        setProdutoReconhecido(resposta.produto);
        setCodigoNovo(null);
        setCadastrandoNovo(false);
        setNomeNovoProd('');
        setUnidadeNovoProd('');
      } else {
        Alert.alert("Erro", "Não foi possível cadastrar.");
      }
    } catch (e) { Alert.alert("Erro", "Sem conexão."); }
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
          onPress={() => { setScanned(false); setEtapaAuth('CAMERA_PAREAMENTO'); }}
        >
          <Text style={[styles.btnTextEscuro, {color: '#fff', fontSize: 18}]}>📷 Vincular Estabelecimento</Text>
          <Text style={{color: '#e0e0e0', fontSize: 13, marginTop: 4}}>Escanear QR Code no Monitor</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // ========================================================
  // TELA 1.5: CÂMERA DE PAREAMENTO (LENDO QR CODE DO PC)
  // ========================================================
  if (etapaAuth === 'CAMERA_PAREAMENTO') {
    return (
      <View style={styles.containerCamera}>
        <CameraView 
          style={StyleSheet.absoluteFillObject} 
          facing="back" 
          onBarcodeScanned={scanned ? undefined : handleBarCodeScanned} 
          barcodeScannerSettings={{ barcodeTypes: ["qr"] }} 
        />
        <View style={styles.overlay}>
          <Text style={styles.textoScan}>Lendo QR Code do Monitor...</Text>
          {scanned && (
            <TouchableOpacity style={[styles.btnConfirmarAuth, {backgroundColor: '#FFD700', marginBottom: 10}]} onPress={() => setScanned(false)}>
               <Text style={styles.btnTextEscuro}>TOCAR PARA LER NOVAMENTE</Text>
            </TouchableOpacity>
          )}
          <TouchableOpacity style={[styles.btnConfirmarAuth, {backgroundColor: '#F44336'}]} onPress={() => setEtapaAuth('INICIO')}>
            <Text style={styles.btnText}>VOLTAR</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  // ========================================================
  // TELA 2: PORTA DE LOGIN UNIFICADA (SENHA OU PIN NA MESMA CAIXA)
  // ========================================================
  if (etapaAuth === 'LOGIN_UNIFICADO') {
    const executarLoginInteligente = () => {
      const credencial = senhaUsuario.trim();
      
      if (!credencial) {
        Alert.alert("Aviso", "Preencha a senha ou o PIN.");
        return;
      }

      // Se for só 4 números, tenta entrar como PIN de funcionário
      if (credencial.length === 4 && /^\d+$/.test(credencial)) {
        fazerLoginAPI_PIN(credencial);
      } else {
        // Se for senha normal, exige o usuário preenchido
        if (!loginUsuario.trim()) {
          Alert.alert("Aviso", "Preencha o usuário.");
          return;
        }
        fazerLoginAPI_Senha(loginUsuario.trim(), credencial);
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
          <Text style={styles.btnTextEscuro}>{carregando ? "Conectando..." : "Conectar"}</Text>
        </TouchableOpacity>

        <TouchableOpacity style={{marginTop: 25}} onPress={() => { 
            AsyncStorage.removeItem('vegastock_cliente_id'); // <-- DELETA DA MEMÓRIA
            setEmpresaPareada(false); 
            setEtapaAuth('INICIO'); 
          }}>
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
      if (cadastrandoNovo) {
        return (
          <View style={styles.containerBranco}>
            <Text style={{fontSize: 28, fontWeight: 'bold', color: '#2196F3', marginBottom: 10}}>Novo Produto</Text>
            <Text style={{fontSize: 16, marginBottom: 20, textAlign: 'center'}}>Cadastrando código: {codigoNovo}</Text>
            
            <TextInput style={[styles.inputAuth, {backgroundColor: '#fff', color: '#000', borderWidth: 2, borderColor: '#ccc'}]} placeholder="Nome (Ex: Cebola Roxa)" placeholderTextColor="#999" value={nomeNovoProd} onChangeText={setNomeNovoProd} />
            <TextInput style={[styles.inputAuth, {backgroundColor: '#fff', color: '#000', borderWidth: 2, borderColor: '#ccc'}]} placeholder="Unidade (Ex: kg, un, litro)" placeholderTextColor="#999" value={unidadeNovoProd} onChangeText={setUnidadeNovoProd} />
            
            <TouchableOpacity style={[styles.btnConfirmarAuth, {backgroundColor: '#4CAF50', width: '90%'}]} onPress={cadastrarProdutoPeloCelular}>
              <Text style={styles.btnText}>SALVAR E CONTINUAR</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.btnConfirmarAuth, {backgroundColor: '#999', width: '90%', marginTop: 10}]} onPress={() => setCadastrandoNovo(false)}>
              <Text style={styles.btnText}>VOLTAR</Text>
            </TouchableOpacity>
          </View>
        );
      }

      return (
        <View style={styles.containerBranco}>
          <Text style={{fontSize: 28, fontWeight: 'bold', color: '#FF9800', marginBottom: 10}}>Código Desconhecido</Text>
          <Text style={{fontSize: 16, marginBottom: 15, textAlign: 'center', paddingHorizontal: 20}}>O código {codigoNovo} não existe no sistema. O que deseja fazer?</Text>
          
          <TouchableOpacity style={[styles.botaoAcao, {backgroundColor: '#2196F3', marginBottom: 15}]} onPress={() => setCadastrandoNovo(true)}>
            <Text style={styles.btnText}>➕ CADASTRAR NOVO PRODUTO</Text>
          </TouchableOpacity>
          
          <Text style={{fontSize: 14, fontWeight: 'bold', marginVertical: 10, color: '#666'}}>OU VINCULAR A UM EXISTENTE:</Text>

          <FlatList data={produtosCatalogo} keyExtractor={(item) => item.id.toString()} style={{ width: '90%', marginBottom: 10 }} renderItem={({ item }) => (
              <TouchableOpacity style={{backgroundColor: '#fff', padding: 15, marginVertical: 4, borderRadius: 8, borderWidth: 1, borderColor: '#ddd'}} onPress={() => realizarBatismo(item.id)}>
                <Text style={{fontSize: 16, fontWeight: 'bold', color: '#333', textAlign: 'center'}}>{item.nome}</Text>
              </TouchableOpacity>
            )} />
          <TouchableOpacity style={[styles.btnConfirmarAuth, {backgroundColor: '#F44336', width: '90%'}]} onPress={() => { setCodigoNovo(null); setScanned(false); }}>
            <Text style={styles.btnText}>CANCELAR TUDO</Text>
          </TouchableOpacity>
        </View>
      );
    }

    if (modo) {
      // Filtra os produtos do catálogo com base no que for digitado
      const produtosFiltrados = produtosCatalogo.filter(p =>
        p.nome.toLowerCase().includes(textoBuscaManual.toLowerCase())
      );

      return modoCamera ? (
        <View style={styles.containerCamera}>
          <CameraView style={StyleSheet.absoluteFillObject} facing="back" onBarcodeScanned={scanned ? undefined : handleBarCodeScanned} barcodeScannerSettings={{ barcodeTypes: ["ean13", "ean8", "qr", "upc_a"] }} />
          <View style={styles.overlay}>
            <Text style={styles.textoScan}>Lendo código para {modo}...</Text>
            {scanned && (
              <TouchableOpacity style={[styles.btnConfirmarAuth, {backgroundColor: '#FFD700', marginBottom: 10}]} onPress={() => setScanned(false)}>
                 <Text style={styles.btnTextEscuro}>TOCAR PARA LER NOVAMENTE</Text>
              </TouchableOpacity>
            )}
            
            {/* NOVO BOTÃO DE BUSCA MANUAL */}
            <TouchableOpacity 
              style={[styles.btnConfirmarAuth, {backgroundColor: '#2196F3', marginBottom: 10}]} 
              onPress={async () => {
                setModoCamera(false);
                // Já garante que a lista de produtos está baixada pra pesquisa
                try {
                  let res = await fetch(`${API_URL}/produtos_mobile/${clienteIdContexto}`);
                  if (res.ok) setProdutosCatalogo(await res.json());
                } catch(e) {}
              }}
            >
              <Text style={styles.btnText}>SEM CÓDIGO? DIGITAR MANUALMENTE</Text>
            </TouchableOpacity>

            <TouchableOpacity style={[styles.btnConfirmarAuth, {backgroundColor: '#F44336'}]} onPress={() => setModo(null)}>
              <Text style={styles.btnText}>VOLTAR</Text>
            </TouchableOpacity>
          </View>
        </View>
      ) : (
        <View style={styles.containerEscuro}>
          <Text style={styles.tituloSecundario}>Busca Manual - {modo}</Text>

          <TextInput
            style={[styles.inputAuth, { marginTop: 20 }]}
            placeholder="Digite o nome do produto..."
            placeholderTextColor="#777"
            value={textoBuscaManual}
            onChangeText={setTextoBuscaManual}
          />

          <FlatList
            data={produtosFiltrados}
            keyExtractor={(item) => item.id.toString()}
            style={{ width: '90%', marginBottom: 20 }}
            renderItem={({ item }) => (
              <TouchableOpacity
                style={{ backgroundColor: '#2b2b36', padding: 15, marginVertical: 5, borderRadius: 8, borderWidth: 1, borderColor: '#444' }}
                onPress={() => {
                  setProdutoReconhecido(item);
                  setTextoBuscaManual('');
                  setModoCamera(true); // Volta a câmera ao normal para a próxima leitura
                }}
              >
                <Text style={{ fontSize: 18, fontWeight: 'bold', color: '#fff' }}>{item.nome}</Text>
              </TouchableOpacity>
            )}
          />

          <TouchableOpacity
            style={[styles.btnConfirmarAuth, {backgroundColor: '#444'}]}
            onPress={() => { setModoCamera(true); setTextoBuscaManual(''); }}
          >
            <Text style={styles.btnText}>VOLTAR PARA A CÂMERA</Text>
          </TouchableOpacity>
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