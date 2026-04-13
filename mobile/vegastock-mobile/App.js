import React, { useState } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, Button } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';

export default function App() {
  // Pede permissão para usar a câmera do celular
  const [permission, requestPermission] = useCameraPermissions();
  
  // Variáveis de Estado (O "cérebro" da tela)
  const [scanned, setScanned] = useState(false);
  const [modo, setModo] = useState(null); // Vai guardar se é 'ENTRADA', 'SAIDA' ou null (Menu Principal)

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

  // A função que roda no EXATO milissegundo que a câmera acha um código de barras
  const handleBarCodeScanned = ({ type, data }) => {
    setScanned(true);
    // Aqui é onde o aplicativo vai gritar pra sua API lá na Render no futuro!
    alert(`Operação: ${modo}\nCódigo Lido: ${data}\n\nO leitor está funcionando perfeitamente!`);
    
    // Volta pro menu principal depois de 2 segundos
    setTimeout(() => {
      setModo(null);
    }, 2000);
  };

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