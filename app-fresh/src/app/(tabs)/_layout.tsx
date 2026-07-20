import { Tabs } from 'expo-router';

export default function TabsLayout() {
  return (
    <Tabs>
      <Tabs.Screen 
        name="(home)" 
        options={{ 
          title: 'Home',
          tabBarLabel: 'Home' 
        }} 
      />
      <Tabs.Screen 
        name="(messages)" 
        options={{ 
          title: 'Messages',
          tabBarLabel: 'Messages' 
        }} 
      />
      <Tabs.Screen 
        name="(profile)" 
        options={{ 
          title: 'Profile',
          tabBarLabel: 'Profile' 
        }} 
      />
    </Tabs>
  );
}
