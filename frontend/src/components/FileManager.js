import React, { useState, useEffect } from 'react';

const FileManager = () => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);

  const loadFiles = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/list_files');
      const data = await response.json();
      setFiles(data.files || []);
    } catch (error) {
      console.error('Error loading files:', error);
    }
    setLoading(false);
  };

  const deleteFile = async (filename) => {
    if (!window.confirm(`确定要删除文件 ${filename} 吗？`)) return;
    
    try {
      const response = await fetch('/api/delete_file', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename })
      });
      
      const data = await response.json();
      if (response.ok) {
        alert(data.message);
        loadFiles(); // 重新加载文件列表
      } else {
        alert(data.error);
      }
    } catch (error) {
      alert('删除文件失败: ' + error.message);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (timestamp) => {
    return new Date(timestamp * 1000).toLocaleString();
  };

  useEffect(() => {
    loadFiles();
  }, []);

  return (
    <div>
      <h2>文件管理</h2>
      <div style={{ marginBottom: '16px' }}>
        <button onClick={loadFiles} disabled={loading}>
          {loading ? '加载中...' : '刷新文件列表'}
        </button>
      </div>
      
      {files.length === 0 ? (
        <p style={{ color: '#666', fontStyle: 'italic' }}>
          暂无文件，请先上传文件到各个功能模块
        </p>
      ) : (
        <div style={{ 
          border: '1px solid #dfe6e9',
          borderRadius: '8px',
          overflow: 'hidden'
        }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead style={{ background: '#f8fafd' }}>
              <tr>
                <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #dfe6e9' }}>
                  文件名
                </th>
                <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #dfe6e9' }}>
                  大小
                </th>
                <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #dfe6e9' }}>
                  修改时间
                </th>
                <th style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #dfe6e9' }}>
                  操作
                </th>
              </tr>
            </thead>
            <tbody>
              {files.map((file, index) => (
                <tr key={index} style={{ 
                  borderBottom: index < files.length - 1 ? '1px solid #dfe6e9' : 'none' 
                }}>
                  <td style={{ padding: '12px' }}>
                    <span style={{ 
                      fontFamily: 'monospace',
                      background: '#f1f3f4',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      fontSize: '13px'
                    }}>
                      {file.name}
                    </span>
                  </td>
                  <td style={{ padding: '12px', color: '#636e72' }}>
                    {formatFileSize(file.size)}
                  </td>
                  <td style={{ padding: '12px', color: '#636e72' }}>
                    {formatDate(file.modified)}
                  </td>
                  <td style={{ padding: '12px', textAlign: 'center' }}>
                    <button
                      onClick={() => deleteFile(file.name)}
                      style={{
                        background: '#e17055',
                        color: 'white',
                        border: 'none',
                        padding: '4px 8px',
                        borderRadius: '4px',
                        fontSize: '12px',
                        cursor: 'pointer'
                      }}
                      onMouseOver={e => e.target.style.background = '#d63031'}
                      onMouseOut={e => e.target.style.background = '#e17055'}
                    >
                      删除
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default FileManager;
