import { Text, View, StyleSheet } from 'react-native';

export default function Index() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>PLACEHOLDER</Text>
      <Text style={styles.subtitle}>If you see this,the app works</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#1a1a2e',
  },
  title: {
    color: '#0f0',
    fontSize: 32,
    fontWeight: 'bold',
  },
  subtitle: {
    color: '#fff',
    fontSize: 16,
    marginTop: 12,
  },
});
