import React, { useState } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, Button, FlatList, TextInput } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';

export default function App() {
  // Pede permissão para usar a câmera do celular
  const [permission, requestPermission] = useCameraPermissions();
  
  // Variáveis de Estado (O "cérebro" da tela)
  const [scanned, setScanned] = useState(false);
  const [modo, setModo] = useState(null); // Vai guardar se é 'ENTRADA', 'SAIDA' ou null (Menu Principal)
  const [codigoNovo, setCodigoNovo] = useState(null);
  const [produtoReconhecido, setProdutoReconhecido] = useState(null);
  const [quantidade, setQuantidade] = useState('');
  const [produtosCatalogo, setProdutosCatalogo] = useState([]);

  // Se ainda tá carregando a permissão
  if (!permission) {
    return <View />;
  }

  // Se o usuário negou a câmera
  if (!permission.granted) {
    return (
      <View style={styles.container}>
        <Text style={{ textAlign: 'center', marginBottom: 20, fontSize: 18 }}>
          Precisamos da sua permissão para usar a câmera no estoque.
        </Text>
        <Button onPress={requestPermission} title="Conceder Permissão" />
      </View>
    );
  }

  // A função que roda no EXATO milissegundo que a câmera acha um código
  const handleBarCodeScanned = async ({ type, data }) => {
    setScanned(true);
    
    // ATENÇÃO: Como não fizemos a tela de Login no celular ainda, 
    // vamos fingir que o João Estoquista logou no restaurante de ID 1.
    const cliente_id_temporario = 1; 
    const API_URL = "https://vegastock.onrender.com";

    try {
      // O Detetive: Vai na Render e pergunta de quem é esse código
      let resposta = await fetch(`${API_URL}/produto_por_codigo/${cliente_id_temporario}/${data}`);

      if (resposta.status === 200) {
        // Cenário A: O Produto já existe e tem esse código!
        let produto = await resposta.json();
        setProdutoReconhecido(produto);
        
      } else if (resposta.status === 404) {
        // Cenário B: O Batismo! O código existe, mas a API não conhece.
        setCodigoNovo(data); // Salva o número na memória para a tela de batismo
        
        // Busca a lista REAL de produtos lá na Render
        try {
          let resProdutos = await fetch(`${API_URL}/produtos_mobile/${cliente_id_temporario}`);
          if (resProdutos.ok) {
            let produtosReais = await resProdutos.json();
            setProdutosCatalogo(produtosReais);
          } else {
            alert("Erro ao buscar a lista de produtos reais.");
          }
        } catch (e) {
          alert("Sem conexão para baixar a lista de produtos.");
        }
        
      } else {
        alert("Erro esquisito na API. Status: " + resposta.status);
      }

    } catch (erro) {
      alert("Falha na conexão! O servidor da Render ainda deve estar reiniciando... tenta de novo em 1 minuto.");
    }

    // Volta pro menu principal depois de 4 segundos
    setTimeout(() => {
      setModo(null);
    }, 4000);
  };

  // Função que atira na sua rota PUT da Render e já pula pra quantidade
  const realizarBatismo = async (produto_id) => {
    try {
      const res = await fetch("https://vegastock.onrender.com/vincular_codigo", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ produto_id: produto_id, codigo_barras: codigoNovo, cliente_id: 1 })
      });

      if (res.ok) {
        alert("✅ Código vinculado com sucesso! O sistema já aprendeu.");
        
        // O PULO DO GATO: Acha qual foi o produto que você clicou na lista
        const produtoEscolhido = produtosCatalogo.find(p => p.id === produto_id);

        setCodigoNovo(null); // Fecha a tela de batismo
        setProdutoReconhecido(produtoEscolhido); // ABRE A TELA DE QUANTIDADE DIRETO!
        
      } else {
        alert("Erro da API ao vincular o código.");
      }
    } catch (error) {
      alert("Sem conexão com o servidor.");
    }
  };

  // Função que envia a quantidade para a nuvem
  const confirmarMovimentacao = async () => {
    if (!quantidade || isNaN(quantidade) || Number(quantidade) <= 0) {
      alert("Digite uma quantidade válida maior que zero!");
      return;
    }

    try {
      const res = await fetch("https://vegastock.onrender.com/movimentar_mobile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          cliente_id: 1,
          produto_id: produtoReconhecido.id,
          tipo_movimento: modo, // 'ENTRADA' ou 'SAIDA'
          quantidade: Number(quantidade)
        })
      });

      if (res.ok) {
        alert(`✅ Sucesso! ${modo} de ${quantidade} registrada no sistema.`);
        setProdutoReconhecido(null); // Fecha a tela
        setQuantidade('');           // Limpa o teclado
        setScanned(false);           // Reseta o leitor
        setModo(null);               // Volta pro menu principal
      } else {
        alert("Erro ao registrar no servidor.");
      }
    } catch (error) {
      alert("Sem conexão com o servidor.");
    }
  };

  // ==========================================
  // TELA 4: DIGITAR A QUANTIDADE (Produto Reconhecido)
  // ==========================================
  if (produtoReconhecido) {
    return (
      <View style={styles.container}>
        <Text style={[styles.titulo, { color: modo === 'ENTRADA' ? '#4CAF50' : '#F44336' }]}>
          {modo}
        </Text>
        
        <Text style={{fontSize: 24, fontWeight: 'bold', marginVertical: 10, textAlign: 'center'}}>
          {produtoReconhecido.nome}
        </Text>
        <Text style={{fontSize: 16, color: 'gray', marginBottom: 30}}>
          Medida em: {produtoReconhecido.unidade_medida}
        </Text>

        <TextInput
          style={{borderWidth: 2, borderColor: '#ccc', width: '60%', fontSize: 40, padding: 15, textAlign: 'center', borderRadius: 10, marginBottom: 30}}
          keyboardType="numeric"
          placeholder="0"
          value={quantidade}
          onChangeText={setQuantidade}
        />

        <View style={{width: '80%'}}>
          <Button title="CONFIRMAR" color={modo === 'ENTRADA' ? '#4CAF50' : '#F44336'} onPress={confirmarMovimentacao} />
          <View style={{marginTop: 15}}>
            <Button title="Cancelar" color="#333" onPress={() => { setProdutoReconhecido(null); setQuantidade(''); setScanned(false); }} />
          </View>
        </View>
      </View>
    );
  }

  // ==========================================
  // TELA 3: A TELA DE BATISMO (LISTA DE PRODUTOS)
  // ==========================================
  if (codigoNovo) {
    return (
      <View style={styles.container}>
        <Text style={styles.titulo}>Código Novo!</Text>
        <Text style={{fontSize: 16, marginBottom: 20}}>O que é o produto de código: {codigoNovo}?</Text>
        
        <FlatList
          data={produtosCatalogo}
          keyExtractor={(item) => item.id.toString()}
          style={{ width: '100%', marginBottom: 20 }}
          renderItem={({ item }) => (
            <TouchableOpacity 
              style={{backgroundColor: '#e0e0e0', padding: 20, marginVertical: 5, borderRadius: 10}}
              onPress={() => realizarBatismo(item.id)}
            >
              <Text style={{fontSize: 18, fontWeight: 'bold'}}>{item.nome}</Text>
            </TouchableOpacity>
          )}
        />
        
        <Button title="Cancelar e Voltar" color="#F44336" onPress={() => { setCodigoNovo(null); setScanned(false); }} />
      </View>
    );
  }

  // ==========================================
  // TELA 2: A CÂMERA LIGADA (O Leitor)
  // ==========================================
  if (modo) {
    return (
      <View style={styles.containerCamera}>
        <CameraView
          style={StyleSheet.absoluteFillObject}
          facing="back"
          onBarcodeScanned={scanned ? undefined : handleBarCodeScanned}
          barcodeScannerSettings={{
            barcodeTypes: ["ean13", "ean8", "qr", "upc_a"], // Os códigos de mercado padrão
          }}
        />
        {/* A interface desenhada por cima da câmera */}
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

  // ==========================================
  // TELA 1: MENU PRINCIPAL
  // ==========================================
  return (
    <View style={styles.container}>
      <Text style={styles.titulo}>VegaStock</Text>
      <Text style={styles.subtitulo}>Terminal do Estoquista</Text>

      <TouchableOpacity 
        style={[styles.botao, styles.btnEntrada]} 
        onPress={() => { setModo('ENTRADA'); setScanned(false); }}
      >
        <Text style={styles.btnText}>⬇️ ENTRADA</Text>
      </TouchableOpacity>

      <TouchableOpacity 
        style={[styles.botao, styles.btnSaida]} 
        onPress={() => { setModo('SAIDA'); setScanned(false); }}
      >
        <Text style={styles.btnText}>⬆️ SAÍDA</Text>
      </TouchableOpacity>
    </View>
  );
}

// ==========================================
// O "CSS" DO APLICATIVO
// ==========================================
const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
    padding: 20,
  },
  containerCamera: {
    flex: 1,
    justifyContent: 'center',
  },
  titulo: {
    fontSize: 40,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 5,
  },
  subtitulo: {
    fontSize: 18,
    color: '#777',
    marginBottom: 60,
  },
  botao: {
    width: '100%',
    padding: 30,
    borderRadius: 15,
    alignItems: 'center',
    marginBottom: 20,
    elevation: 5, // Sombra no Android
    shadowColor: '#000', // Sombra no iOS
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
  },
  btnEntrada: {
    backgroundColor: '#4CAF50',
  },
  btnSaida: {
    backgroundColor: '#F44336',
  },
  btnText: {
    color: '#fff',
    fontSize: 28,
    fontWeight: 'bold',
  },
  overlay: {
    flex: 1,
    backgroundColor: 'transparent',
    justifyContent: 'flex-end',
    padding: 20,
    marginBottom: 30,
  },
  textoScan: {
    backgroundColor: 'rgba(0,0,0,0.8)',
    color: 'white',
    padding: 15,
    textAlign: 'center',
    fontSize: 20,
    fontWeight: 'bold',
    borderRadius: 8,
    marginBottom: 20,
  },
  btnVoltar: {
    backgroundColor: '#333',
    padding: 20,
    borderRadius: 10,
    alignItems: 'center',
    marginTop: 10,
  },
  btnTextPequeno: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  }
});