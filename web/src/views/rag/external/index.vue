<template>
  <div class="external-rag-page">
    <PageWrapper title="TrustRAG 外部服务" content="基于 TrustRAG 的智能问答和知识检索系统">
      <template #headerContent>
        <a-space>
          <a-tag color="blue">外部服务</a-tag>
          <a-tag color="green">智能问答</a-tag>
          <a-tag color="orange">知识检索</a-tag>
        </a-space>
      </template>
      
      <!-- 服务状态 -->
      <ServiceStatus />
      
      <!-- 功能区域 -->
      <a-row :gutter="16" style="margin-top: 16px">
        <a-col :span="12">
          <ChatInterface />
        </a-col>
        <a-col :span="12">
          <KnowledgeSearch />
        </a-col>
      </a-row>
      
      <!-- 使用说明 -->
      <a-card title="使用说明" :bordered="false" style="margin-top: 16px">
        <a-collapse v-model:activeKey="activeKeys" ghost>
          <a-collapse-panel key="1" header="快速开始">
            <div class="help-content">
              <h4>🚀 快速开始</h4>
              <ol>
                <li><strong>检查服务状态</strong>：确保 TrustRAG 服务正常运行</li>
                <li><strong>初始化服务</strong>：如果状态显示"初始化中"，点击"初始化服务"按钮</li>
                <li><strong>开始对话</strong>：在左侧聊天界面输入问题，或点击预设问题</li>
                <li><strong>知识检索</strong>：在右侧搜索界面输入关键词进行知识检索</li>
              </ol>
            </div>
          </a-collapse-panel>
          
          <a-collapse-panel key="2" header="功能特性">
            <div class="help-content">
              <h4>✨ 功能特性</h4>
              <ul>
                <li><strong>智能问答</strong>：基于汽车操作手册的智能问答系统</li>
                <li><strong>知识检索</strong>：支持关键词检索和相似度匹配</li>
                <li><strong>预设问题</strong>：提供常见问题的快速访问</li>
                <li><strong>对话管理</strong>：支持对话导出、清空、重新生成等</li>
                <li><strong>搜索统计</strong>：提供搜索次数、响应时间等统计信息</li>
              </ul>
            </div>
          </a-collapse-panel>
          
          <a-collapse-panel key="3" header="使用技巧">
            <div class="help-content">
              <h4>💡 使用技巧</h4>
              <ul>
                <li><strong>问题描述</strong>：尽量详细描述问题，获得更准确的答案</li>
                <li><strong>相似度阈值</strong>：调整阈值可以控制检索结果的精确度</li>
                <li><strong>自动检索</strong>：开启自动检索可以实时获得结果</li>
                <li><strong>结果导出</strong>：可以导出对话记录和搜索结果</li>
                <li><strong>快捷键</strong>：使用 Ctrl+Enter 快速发送消息</li>
              </ul>
            </div>
          </a-collapse-panel>
          
          <a-collapse-panel key="4" header="常见问题">
            <div class="help-content">
              <h4>❓ 常见问题</h4>
              <a-collapse size="small" ghost>
                <a-collapse-panel key="q1" header="服务连接失败怎么办？">
                  <p>请检查：</p>
                  <ul>
                    <li>TrustRAG 服务是否已启动</li>
                    <li>端口 8217 是否被占用</li>
                    <li>网络连接是否正常</li>
                  </ul>
                </a-collapse-panel>
                
                <a-collapse-panel key="q2" header="搜索无结果怎么办？">
                  <p>可以尝试：</p>
                  <ul>
                    <li>降低相似度阈值</li>
                    <li>增加结果数量</li>
                    <li>使用不同的关键词</li>
                    <li>检查服务是否已初始化</li>
                  </ul>
                </a-collapse-panel>
                
                <a-collapse-panel key="q3" header="如何获得更好的答案？">
                  <p>建议：</p>
                  <ul>
                    <li>使用具体的问题描述</li>
                    <li>参考预设问题格式</li>
                    <li>如果答案不满意，可以重新生成</li>
                    <li>结合知识检索功能获得更多信息</li>
                  </ul>
                </a-collapse-panel>
              </a-collapse>
            </div>
          </a-collapse-panel>
        </a-collapse>
      </a-card>
    </PageWrapper>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { PageWrapper } from '/@/components/Page';
import ServiceStatus from './components/ServiceStatus.vue';
import ChatInterface from './components/ChatInterface.vue';
import KnowledgeSearch from './components/KnowledgeSearch.vue';

const activeKeys = ref(['1']);
</script>

<style scoped>
.external-rag-page {
  padding: 16px;
}

.help-content {
  padding: 8px 0;
}

.help-content h4 {
  margin-bottom: 16px;
  color: #1890ff;
}

.help-content ol,
.help-content ul {
  padding-left: 20px;
}

.help-content li {
  margin-bottom: 8px;
  line-height: 1.6;
}

.help-content strong {
  color: #333;
}

:deep(.ant-collapse-header) {
  font-weight: 500;
}

:deep(.ant-collapse-content-box) {
  padding: 16px 0;
}
</style>
