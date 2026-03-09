<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NLayout, NLayoutSider, NMenu, NIcon, NButton, NTooltip } from 'naive-ui'
import type { MenuOption } from 'naive-ui'
import {
  HomeOutline,
  BookOutline,
  FolderOutline,
  StatsChartOutline,
  MenuOutline,
  ChevronBackOutline,
  SettingsOutline,
} from '@vicons/ionicons5'
import { h } from 'vue'

const route = useRoute()
const router = useRouter()
const collapsed = ref(false)
const isMobile = ref(false)

function checkMobile() {
  isMobile.value = window.innerWidth <= 768
  if (isMobile.value) {
    collapsed.value = true
  }
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})

function renderIcon(icon: any) {
  return () => h(NIcon, null, { default: () => h(icon) })
}

const menuOptions: MenuOption[] = [
  {
    label: '仪表盘',
    key: 'home',
    icon: renderIcon(HomeOutline),
  },
  {
    label: '日记列表',
    key: 'diaries',
    icon: renderIcon(BookOutline),
  },
  {
    label: '项目管理',
    key: 'projects',
    icon: renderIcon(FolderOutline),
  },
  {
    label: '统计概览',
    key: 'stats',
    icon: renderIcon(StatsChartOutline),
  },
  {
    label: '系统设置',
    key: 'settings',
    icon: renderIcon(SettingsOutline),
  },
]

const activeKey = computed(() => {
  const name = route.name as string
  if (name === 'diary-detail') return 'diaries'
  return name || 'home'
})

const mainMarginLeft = computed(() => {
  if (isMobile.value) return '0px'
  return collapsed.value ? '64px' : '240px'
})

function handleMenuUpdate(key: string) {
  router.push({ name: key })
  if (isMobile.value) {
    collapsed.value = true
  }
}

function handleOverlayClick() {
  if (isMobile.value) {
    collapsed.value = true
  }
}
</script>

<template>
  <NLayout has-sider class="min-h-screen">
    <!-- Mobile overlay -->
    <div
      v-if="isMobile && !collapsed"
      class="mobile-overlay"
      @click="handleOverlayClick"
    />

    <!-- Sidebar -->
    <NLayoutSider
      bordered
      :collapsed="collapsed"
      collapse-mode="width"
      :collapsed-width="isMobile ? 0 : 64"
      :width="240"
      :native-scrollbar="false"
      class="sidebar"
      :class="{ 'sidebar-mobile': isMobile, 'sidebar-mobile-visible': isMobile && !collapsed }"
    >
      <!-- Logo -->
      <div class="logo-area" :class="{ collapsed }">
        <div class="logo-icon">📝</div>
        <transition name="fade">
          <span v-if="!collapsed" class="logo-text">DevDiary</span>
        </transition>
      </div>

      <!-- Navigation Menu -->
      <NMenu
        :collapsed="collapsed"
        :collapsed-width="64"
        :collapsed-icon-size="22"
        :options="menuOptions"
        :value="activeKey"
        @update:value="handleMenuUpdate"
        class="nav-menu"
      />

      <!-- Collapse toggle -->
      <div class="collapse-toggle" v-if="!isMobile">
        <NTooltip placement="right">
          <template #trigger>
            <NButton
              text
              @click="collapsed = !collapsed"
              class="collapse-btn"
            >
              <NIcon size="20">
                <ChevronBackOutline v-if="!collapsed" />
                <MenuOutline v-else />
              </NIcon>
            </NButton>
          </template>
          {{ collapsed ? '展开侧栏' : '收起侧栏' }}
        </NTooltip>
      </div>
    </NLayoutSider>

    <!-- Main Content -->
    <NLayout class="main-layout" :style="{ marginLeft: mainMarginLeft }">
      <!-- Mobile header -->
      <div v-if="isMobile" class="mobile-header">
        <NButton text @click="collapsed = !collapsed">
          <NIcon size="24"><MenuOutline /></NIcon>
        </NButton>
        <span class="mobile-title">DevDiary</span>
      </div>

      <div class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="page" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </NLayout>
  </NLayout>
</template>

<style scoped>
.sidebar {
  background: rgba(15, 23, 42, 0.95) !important;
  backdrop-filter: blur(20px);
  border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  bottom: 0;
  z-index: 100;
}

.sidebar-mobile {
  z-index: 1001;
  transform: translateX(-100%);
  transition: transform 0.3s ease;
}

.sidebar-mobile-visible {
  transform: translateX(0);
}

.mobile-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1000;
}

.mobile-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(15, 23, 42, 0.95);
  backdrop-filter: blur(20px);
  position: sticky;
  top: 0;
  z-index: 50;
}

.mobile-title {
  font-size: 18px;
  font-weight: 700;
  background: linear-gradient(135deg, #6366F1, #A78BFA);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.logo-area {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  min-height: 64px;
  transition: all 0.3s ease;
}
.logo-area.collapsed {
  justify-content: center;
  padding: 20px 0;
}

.logo-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.logo-text {
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(135deg, #6366F1, #A78BFA);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  white-space: nowrap;
}

.nav-menu {
  flex: 1;
  padding-top: 8px;
}

.nav-menu :deep(.n-menu-item-content) {
  border-radius: 8px !important;
  margin: 2px 8px !important;
}

.nav-menu :deep(.n-menu-item-content::before) {
  border-radius: 8px !important;
}

.nav-menu :deep(.n-menu-item-content--selected::before) {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(139, 92, 246, 0.1)) !important;
  border-left: 3px solid #6366F1;
}

.collapse-toggle {
  padding: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  justify-content: center;
}

.collapse-btn {
  color: #94A3B8;
  transition: color 0.3s;
}
.collapse-btn:hover {
  color: #A78BFA;
}

.main-layout {
  background: transparent !important;
  transition: margin-left 0.3s ease;
}

.main-content {
  padding: 32px;
  min-height: 100vh;
  max-width: 1400px;
  margin: 0 auto;
}

/* Page transition */
.page-enter-active,
.page-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.page-enter-from {
  opacity: 0;
  transform: translateY(10px);
}
.page-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* Fade transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 768px) {
  .main-content {
    padding: 16px;
  }
}
</style>
