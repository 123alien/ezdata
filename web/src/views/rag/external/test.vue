<template>
  <div class="test-page">
    <h1>TrustRAG 测试页面</h1>
    <p>如果你能看到这个页面，说明路由系统工作正常！</p>
    <a-button type="primary" @click="goBack">返回</a-button>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';

const router = useRouter();

const goBack = () => {
  router.go(-1);
};
</script>

<style scoped>
.test-page {
  padding: 50px;
  text-align: center;
}

h1 {
  color: #1890ff;
  margin-bottom: 20px;
}

p {
  font-size: 16px;
  margin-bottom: 30px;
}
</style>
